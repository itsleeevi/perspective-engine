"""Turn a VideoProject into fixture + stills + spec the existing runners understand."""

from __future__ import annotations

import json
import re
import textwrap
from pathlib import Path

from channel.bibles import token_for_location, visual_lock
from channel.config import (
    CHANNEL,
    config_for_project,
    kokoro_pauses_for,
    kokoro_speed_for,
    kokoro_voice_for,
    visual_accent_for,
)
from channel.metadata import draft_metadata
from channel.engine import (
    PROMPT_VERSION,
    VIDEO_ENGINE_VERSION,
    VISUAL_STYLE_VERSION,
    generate_image_filename,
    image_token_for,
)
from channel.paths import (
    ROOT,
    fixture_path,
    jobs_path,
    relpath_for_spec,
    short_fixture_path,
    short_stills_path,
    spec_path,
    stills_path,
)
from channel.prompts import assemble_image_prompt, format_flow_prompt, strip_character_names, strip_image_brands
from channel.quality_bar import STAGING_QUALITY
from channel.schema import Scene, ScenePurpose, VideoProject
from channel.shorts import (
    SHORT_CTA,
    attach_short_cta_scene,
    ensure_short_cta,
    is_short_cta,
    strip_short_cta,
)


def fixture_dict(project: VideoProject, *, short: bool = False) -> dict:
    if not project.story:
        raise ValueError("project has no story — run the Story Architect first")
    if short:
        if not project.short:
            raise ValueError("project has no short")
        body = strip_short_cta(ensure_short_cta(project.short.short_narration.strip()))
        parts = re.split(r"(?<=[.!?])\s+", body, maxsplit=1)
        hook_s = parts[0]
        rest = parts[1] if len(parts) > 1 else ""
        levels = []
        if rest:
            levels.append({"name": "The Short", "beats": [rest]})
        levels.append({"name": "The Link", "beats": [SHORT_CTA]})
        return {
            "title": project.short.short_title or project.title,
            "hero_career_progression": False,
            "include_level_titles": False,
            "the_thought": project.story.title_payoff,
            "hook": hook_s,
            "levels": levels,
        }
    levels = [
        {"name": ch.name, "beats": [ch.narration]}
        for ch in project.story.chapters
        if ch.narration.strip()
    ]
    if not levels:
        raise ValueError("story has no chapter narration")
    hook = project.story.hook.strip()
    bridge = project.story.next_video_bridge.strip()
    if bridge:
        levels[-1]["beats"].append(bridge)
    return {
        "title": project.title,
        "hero_career_progression": False,
        "include_level_titles": False,
        "title_style": "chapter",
        "speak_title_cards": False,
        "the_thought": project.story.title_payoff,
        "hook": hook,
        "levels": levels,
    }


def _split(beat: str, project: VideoProject | None = None) -> list[str]:
    from graph.script_fixture import split_beat_into_chunks

    cfg = config_for_project(project) if project else CHANNEL
    return split_beat_into_chunks(
        beat,
        wpm=cfg.narration_wpm,
        min_seconds=cfg.min_scene_duration,
        max_seconds=cfg.max_scene_duration,
        target_seconds=cfg.visual_change_target_seconds,
    )


def _chunks_for(fixture: dict, project: VideoProject | None = None) -> list[str]:
    from graph.script_fixture import fixture_to_beats, is_title_beat

    return [
        c
        for beat in fixture_to_beats(fixture, include_hook=True)
        if not is_title_beat(beat)
        for c in _split(beat, project)
    ]


def chunk_list(project: VideoProject, *, short: bool = False) -> list[str]:
    return _chunks_for(fixture_dict(project, short=short), project)


def _py_str(s: str) -> str:
    return json.dumps(s, ensure_ascii=False)


def _prop_token(name: str) -> str:
    token = re.sub(r"[^A-Z0-9]+", "_", name.upper()).strip("_")
    if not token.startswith("THE_"):
        token = f"THE_{token}"
    return token


def stills_module_source(project: VideoProject, scenes: list[Scene]) -> str:
    cfg = config_for_project(project)
    style = strip_image_brands(
        strip_character_names(
            " ".join(
                p
                for p in (
                    cfg.visual_style,
                    visual_accent_for(project.slug, project.channel_mode),
                    cfg.negative_style,
                    STAGING_QUALITY,
                    *[visual_lock(c) for c in project.characters.values()],
                )
                if p
            ),
            project,
        )
    )
    rows = []
    for scene in scenes:
        loc_tok = token_for_location(scene.location) if scene.location else ""
        action = scene.action
        if loc_tok and loc_tok not in action:
            action = f"{loc_tok} {action}"
        rows.append(
            f"    ({_py_str(scene.composition)}, {_py_str(scene.who)}, {_py_str(action)}),"
        )
    set_tokens = [token_for_location(lid) for lid in project.locations]
    prop: dict[str, int] = {}
    if project.story and project.story.signature_prop:
        prop[_prop_token(project.story.signature_prop)] = 6
    return textwrap.dedent(
        f'''\
        """Auto-generated stills for {project.slug}. Do not hardcode a person here;
        character looks come from the project bible frozen below."""

        from __future__ import annotations

        PROP_BUDGET = {prop!r}
        SET_TOKENS = {set_tokens!r}

        STYLE = {_py_str(style)}

        STILLS: list[tuple[str, str, str]] = [
        '''
    ) + "\n".join(rows) + textwrap.dedent(
        """

        ]


        def prompt_for(who: str, scene: str) -> str:
            extra = "STRICTLY NO people, NO faces, NO hands." if who == "empty" else (
                "Only named characters. Same cartoon construction every time."
            )
            return f"{STYLE} {extra} SCENE: {scene}"
        """
    )


def spec_dict(
    project: VideoProject,
    *,
    root: Path | None = None,
    image_token: str | None = None,
) -> dict:
    slug = project.slug
    cfg = config_for_project(project)
    meta = draft_metadata(project)
    token = image_token or image_token_for(slug)
    isolated = root is not None
    if isolated:
        stills_dir = relpath_for_spec(root / "images", root=root)
        output = relpath_for_spec(root / "final" / f"{slug}.mp4", root=root)
    else:
        stills_dir = f"assets/grok_{slug}_v1"
        output = f"assets/output/{slug}.mp4"
    spec = {
        "engine": "channel",
        "engine_version": VIDEO_ENGINE_VERSION,
        "prompt_version": PROMPT_VERSION,
        "visual_style_version": VISUAL_STYLE_VERSION,
        "image_token": token,
        "channel": cfg.name,
        "channel_mode": project.channel_mode.value,
        "topic": project.title,
        "fixture": relpath_for_spec(fixture_path(slug, root), root=root),
        "stills_module": relpath_for_spec(stills_path(slug, root), root=root),
        "image_jobs": relpath_for_spec(jobs_path(f"{slug}_v1_", root), root=root),
        "still_prefix": f"{slug}_v1_",
        "stills_dir": stills_dir,
        "output": output,
        "thread_id": f"{slug}-v1",
        "voice": "imported",
        "imported_audio": (
            relpath_for_spec(root / "audio" / "voiceover.wav", root=root)
            if isolated
            else "audio/voiceover.wav"
        ),
        "timestamps": (
            relpath_for_spec(root / "timestamps.json", root=root)
            if isolated
            else "timestamps.json"
        ),
        "flow_prompts": (
            relpath_for_spec(root / "flow_prompts.txt", root=root)
            if isolated
            else "flow_prompts.txt"
        ),
        "kokoro_voice": kokoro_voice_for(slug),
        "kokoro_speed": kokoro_speed_for(slug, cfg),
        "kokoro_sentence_pause": kokoro_pauses_for(slug, cfg)[0],
        "kokoro_clause_pause": kokoro_pauses_for(slug, cfg)[1],
        "kokoro_pack_words": cfg.kokoro_pack_words,
        "kokoro_scene_pause": kokoro_pauses_for(slug, cfg)[2],
        "narration_wpm": cfg.narration_wpm,
        "burn_captions": cfg.burn_captions,
        "chunk_min_seconds": cfg.min_scene_duration,
        "chunk_max_seconds": cfg.max_scene_duration,
        "chunk_target_seconds": cfg.visual_change_target_seconds,
        "youtube": meta.model_dump(),
    }
    if cfg.default_short_enabled and project.short:
        if isolated:
            short_dir = relpath_for_spec(root / "images" / "short", root=root)
            short_out = relpath_for_spec(
                root / "short" / f"{slug}_short.mp4", root=root
            )
        else:
            short_dir = f"assets/grok_{slug}_short_v1"
            short_out = f"assets/output/{slug}_short.mp4"
        spec["short"] = {
            "fixture": relpath_for_spec(short_fixture_path(slug, root), root=root),
            "stills_module": relpath_for_spec(short_stills_path(slug, root), root=root),
            "image_jobs": relpath_for_spec(
                jobs_path(f"{slug}_short_v1_", root), root=root
            ),
            "still_prefix": f"{slug}_short_v1_",
            "stills_dir": short_dir,
            "output": short_out,
        }
    return spec


def _load_job_timestamps(root: Path | None) -> dict | None:
    if root is None:
        return None
    path = root / "timestamps.json"
    if not path.is_file():
        return None
    from channel.pauses import load_timestamps

    return load_timestamps(path)


def write_flow_prompts(
    project: VideoProject,
    scenes: list[Scene],
    *,
    root: Path | None = None,
) -> Path:
    dest = (root or ROOT) / "flow_prompts.txt"
    dest.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        format_flow_prompt(project, scene, start_seconds=scene.start_seconds)
        for scene in scenes
    ]
    dest.write_text("\n\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
    # ZAPI FLOW upload: one prompt per line, no blank lines.
    batches = (root or ROOT) / "flow_batches.txt"
    one_line = [re.sub(r"\s+", " ", line).strip() for line in lines if line.strip()]
    batches.write_text("\n".join(one_line) + ("\n" if one_line else ""), encoding="utf-8")
    return dest


def write_thumbnail_prompts(project: VideoProject, *, root: Path | None = None) -> Path:
    from channel.youtube import thumbnail_prompt

    dest = (root or ROOT) / "thumbnail_prompts.txt"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(thumbnail_prompt(project).strip() + "\n", encoding="utf-8")
    return dest


def write_jobs(
    spec: dict,
    scenes: list[Scene],
    project: VideoProject,
    *,
    short: bool,
    root: Path | None = None,
    timestamps: dict | None = None,
) -> Path:
    from channel.character_locks import reference_image_paths
    from channel.pauses import expected_image_name
    from graph.script_fixture import fixture_to_beats, is_title_beat, load_fixture

    block = spec["short"] if short else spec
    token = str(spec.get("image_token") or image_token_for(project.slug))
    kind = "short_scene" if short else "scene"
    aspect = "9:16" if short else "16:9"
    prefix = block["still_prefix"]
    rows: list[tuple[Scene, str, str]]
    if timestamps and not short:
        ts_scenes = list(timestamps.get("scenes") or [])
        if len(scenes) != len(ts_scenes):
            raise ValueError(
                f"jobs: {len(scenes)} scenes vs {len(ts_scenes)} pause timestamps"
            )
        rows = []
        for scene, row in zip(scenes, ts_scenes, strict=True):
            dest_name = str(row.get("filename") or expected_image_name(int(row["index"]), float(row["start"])))
            chunk = str(row.get("text") or scene.narration)
            rows.append((scene, chunk, dest_name))
    else:
        data = load_fixture(str((root or ROOT) / block["fixture"]))
        chunks = [
            c
            for beat in fixture_to_beats(data, include_hook=True)
            if not is_title_beat(beat)
            for c in _split(beat, project)
        ]
        if len(scenes) != len(chunks):
            raise ValueError(
                f"jobs: {len(scenes)} scenes vs {len(chunks)} chunks "
                f"({'short' if short else 'long'})"
            )
        pairs = [
            (scene, chunk)
            for scene, chunk in zip(scenes, chunks, strict=True)
            if not is_short_cta(chunk)
        ]
        rows = [
            (scene, chunk, f"{prefix}{i:03d}.png")
            for i, (scene, chunk) in enumerate(pairs)
        ]
    jobs = []
    for i, (scene, chunk, dest_name) in enumerate(rows):
        gen_name = generate_image_filename(i, token=token, kind=kind)
        job = {
            "id": f"{i:03d}",
            "filename": dest_name,
            "generate_filename": gen_name,
            "copy_to": dest_name,
            "aspect": aspect,
            "who": scene.who,
            "free": scene.who == "empty",
            "shot_type": scene.composition,
            "chunk": chunk,
            "scene": scene.action,
            "prompt": format_flow_prompt(project, scene, start_seconds=scene.start_seconds, aspect=aspect)
            if timestamps and not short
            else assemble_image_prompt(project, scene, aspect=aspect),
            "camera_motion": scene.camera_motion,
            "start_seconds": scene.start_seconds,
            "end_seconds": scene.end_seconds,
        }
        refs = reference_image_paths(project, scene, root=root)
        if refs:
            job["reference_image_paths"] = refs
        jobs.append(job)
    out = jobs_path(prefix, root)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"jobs": jobs}, indent=2) + "\n", encoding="utf-8")
    return out


def stub_scenes(project: VideoProject, chunks: list[str]) -> list[Scene]:
    subject = next((c.id for c in project.characters.values() if c.is_subject), "")
    loc = next(iter(project.locations), "")
    out: list[Scene] = []
    for i, chunk in enumerate(chunks):
        who = "hero" if i % 3 != 1 else "empty"
        purpose = ScenePurpose.context
        if project.story and project.story.chapters:
            purpose = project.story.chapters[min(i, len(project.story.chapters) - 1)].purpose
        out.append(
            Scene(
                scene_id=f"scene_{i:03d}",
                narration=chunk,
                purpose=purpose,
                action=f"Visualize: {chunk}",
                composition="medium shot" if who == "hero" else "wide shot",
                characters=[subject] if who == "hero" and subject else [],
                location=loc,
                who=who,
            )
        )
    return out


def stub_scenes_from_timestamps(project: VideoProject, timestamps: dict) -> list[Scene]:
    rows = list(timestamps.get("scenes") or [])
    chunks = [str(row.get("text") or "") for row in rows]
    scenes = stub_scenes(project, chunks)
    for scene, row in zip(scenes, rows, strict=True):
        scene.start_seconds = float(row["start"])
        scene.end_seconds = float(row["end"])
        scene.narration = str(row.get("text") or scene.narration)
    return scenes


def _write_script_artifacts(
    project: VideoProject,
    *,
    root: Path | None,
    token: str,
) -> tuple[dict, dict[str, str]]:
    slug = project.slug
    project.metadata = draft_metadata(project)
    fixture = fixture_dict(project)
    fx = fixture_path(slug, root)
    fx.parent.mkdir(parents=True, exist_ok=True)
    fx.write_text(json.dumps(fixture, indent=2) + "\n", encoding="utf-8")
    spec = spec_dict(project, root=root, image_token=token)
    sp = spec_path(slug, root)
    sp.parent.mkdir(parents=True, exist_ok=True)
    sp.write_text(json.dumps(spec, indent=2) + "\n", encoding="utf-8")
    from channel.youtube import write_pack, write_thumbnail_job

    written = {
        "fixture": str(fx),
        "spec": str(sp),
        "thumbnail_job": str(write_thumbnail_job(project, root=root, image_token=token)),
        "thumbnail_prompts": str(write_thumbnail_prompts(project, root=root)),
        "youtube_description": write_pack(spec, root=root)["description"],
    }
    return spec, written


def compile_project(
    project: VideoProject,
    *,
    stubs_ok: bool = False,
    root: Path | None = None,
    image_token: str | None = None,
    timestamps: dict | None = None,
    stage: str = "auto",
) -> dict[str, str]:
    if not project.story:
        raise ValueError("cannot compile without a story")
    from channel.character_locks import apply_character_locks

    apply_character_locks(project)
    slug = project.slug
    token = image_token or image_token_for(slug)
    table = timestamps
    if stage == "script":
        table = None
    elif table is None:
        table = _load_job_timestamps(root)
    spec, written = _write_script_artifacts(project, root=root, token=token)

    if table is not None:
        scenes = list(project.scenes)
        n = len(table.get("scenes") or [])
        if len(scenes) != n:
            if not stubs_ok:
                raise ValueError(
                    f"scene count {len(scenes)} != {n} pause timestamps. "
                    "Fill scenes 1:1 with timestamps.json after ingest-audio."
                )
            scenes = stub_scenes_from_timestamps(project, table)
            project.scenes = scenes
        else:
            for scene, row in zip(scenes, table["scenes"], strict=True):
                if scene.start_seconds is None:
                    scene.start_seconds = float(row["start"])
                if scene.end_seconds is None:
                    scene.end_seconds = float(row["end"])
                if not scene.narration.strip():
                    scene.narration = str(row.get("text") or "")
        stills_path(slug, root).write_text(stills_module_source(project, scenes), encoding="utf-8")
        written["stills"] = str(stills_path(slug, root))
        written["flow_prompts"] = str(write_flow_prompts(project, scenes, root=root))
        written["jobs"] = str(
            write_jobs(spec, scenes, project, short=False, root=root, timestamps=table)
        )
        return written

    if project.scenes and not stubs_ok:
        raise ValueError(
            "scenes before audio — ingest the voiceover first, then write one scene per pause"
        )

    if stubs_ok:
        fixture = fixture_dict(project)
        chunks = _chunks_for(fixture, project)
        scenes = stub_scenes(project, chunks)
        stills_path(slug, root).write_text(stills_module_source(project, scenes), encoding="utf-8")
        written["stills"] = str(stills_path(slug, root))
        written["jobs"] = str(write_jobs(spec, scenes, project, short=False, root=root))
        cfg = config_for_project(project)
        if cfg.default_short_enabled and project.short:
            sf = fixture_dict(project, short=True)
            short_chunks = _chunks_for(sf, project)
            short_scenes = attach_short_cta_scene(
                stub_scenes(project, short_chunks), short_chunks
            )
            sfp = short_fixture_path(slug, root)
            sfp.write_text(json.dumps(sf, indent=2) + "\n", encoding="utf-8")
            short_stills_path(slug, root).write_text(
                stills_module_source(project, short_scenes), encoding="utf-8"
            )
            write_jobs(spec, short_scenes, project, short=True, root=root)
            written["short_fixture"] = str(sfp)
            from channel.shorts import write_short_thumbnail_job

            written["short_thumbnail_job"] = str(
                write_short_thumbnail_job(project, root=root, image_token=token)
            )
    return written

