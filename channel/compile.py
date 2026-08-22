"""Turn a VideoProject into fixture + stills + spec the existing runners understand."""

from __future__ import annotations

import json
import re
import textwrap
from pathlib import Path

from channel.bibles import token_for_location, visual_lock
from channel.config import CHANNEL
from channel.metadata import draft_metadata
from channel.paths import (
    ROOT,
    fixture_path,
    jobs_path,
    short_fixture_path,
    short_stills_path,
    spec_path,
    stills_path,
)
from channel.prompts import assemble_image_prompt, strip_character_names
from channel.schema import Scene, ScenePurpose, VideoProject


def fixture_dict(project: VideoProject, *, short: bool = False) -> dict:
    if not project.story:
        raise ValueError("project has no story — run the Story Architect first")
    if short:
        if not project.short:
            raise ValueError("project has no short")
        return {
            "title": project.short.short_title or project.title,
            "hero_career_progression": False,
            "include_level_titles": False,
            "the_thought": project.story.title_payoff,
            "hook": project.short.short_narration,
            "levels": [{"name": "The Short", "beats": [project.short.short_narration]}],
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
        "include_level_titles": True,
        "title_style": "chapter",
        "speak_title_cards": False,
        "the_thought": project.story.title_payoff,
        "hook": hook,
        "levels": levels,
    }


def _split(beat: str) -> list[str]:
    from graph.script_fixture import split_beat_into_chunks

    return split_beat_into_chunks(
        beat,
        wpm=CHANNEL.narration_wpm,
        min_seconds=CHANNEL.min_scene_duration,
        max_seconds=CHANNEL.max_scene_duration,
        target_seconds=CHANNEL.visual_change_target_seconds,
    )


def _chunks_for(fixture: dict) -> list[str]:
    from graph.script_fixture import fixture_to_beats, is_title_beat

    return [
        c
        for beat in fixture_to_beats(fixture, include_hook=True)
        if not is_title_beat(beat)
        for c in _split(beat)
    ]


def chunk_list(project: VideoProject, *, short: bool = False) -> list[str]:
    return _chunks_for(fixture_dict(project, short=short))


def _py_str(s: str) -> str:
    return json.dumps(s, ensure_ascii=False)


def _prop_token(name: str) -> str:
    token = re.sub(r"[^A-Z0-9]+", "_", name.upper()).strip("_")
    if not token.startswith("THE_"):
        token = f"THE_{token}"
    return token


def stills_module_source(project: VideoProject, scenes: list[Scene]) -> str:
    style = strip_character_names(
        " ".join(
            [
                CHANNEL.visual_style,
                CHANNEL.negative_style,
                *[visual_lock(c) for c in project.characters.values()],
            ]
        ),
        project,
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


def spec_dict(project: VideoProject, *, root: Path | None = None) -> dict:
    slug = project.slug
    meta = draft_metadata(project)
    base = root or ROOT
    spec = {
        "engine": "channel",
        "channel": CHANNEL.name,
        "topic": project.title,
        "fixture": str(fixture_path(slug, root).relative_to(base)),
        "stills_module": str(stills_path(slug, root).relative_to(base)),
        "still_prefix": f"{slug}_v1_",
        "stills_dir": f"assets/grok_{slug}_v1",
        "thread_id": f"{slug}-v1",
        "voice": CHANNEL.voice,
        "kokoro_voice": CHANNEL.kokoro_voice,
        "kokoro_speed": CHANNEL.kokoro_speed,
        "kokoro_sentence_pause": CHANNEL.kokoro_sentence_pause,
        "kokoro_clause_pause": CHANNEL.kokoro_clause_pause,
        "narration_wpm": CHANNEL.narration_wpm,
        "chunk_min_seconds": CHANNEL.min_scene_duration,
        "chunk_max_seconds": CHANNEL.max_scene_duration,
        "chunk_target_seconds": CHANNEL.visual_change_target_seconds,
        "youtube": meta.model_dump(),
    }
    if CHANNEL.default_short_enabled and project.short:
        spec["short"] = {
            "fixture": str(short_fixture_path(slug, root).relative_to(base)),
            "stills_module": str(short_stills_path(slug, root).relative_to(base)),
            "still_prefix": f"{slug}_short_v1_",
            "stills_dir": f"assets/grok_{slug}_short_v1",
            "output": f"assets/output/{slug}_short.mp4",
        }
    return spec


def write_jobs(
    spec: dict,
    scenes: list[Scene],
    project: VideoProject,
    *,
    short: bool,
    root: Path | None = None,
) -> Path:
    from graph.script_fixture import fixture_to_beats, is_title_beat, load_fixture

    block = spec["short"] if short else spec
    data = load_fixture(str((root or ROOT) / block["fixture"]))
    chunks = [
        c
        for beat in fixture_to_beats(data, include_hook=True)
        if not is_title_beat(beat)
        for c in _split(beat)
    ]
    if len(scenes) != len(chunks):
        raise ValueError(
            f"jobs: {len(scenes)} scenes vs {len(chunks)} chunks "
            f"({'short' if short else 'long'})"
        )
    prefix = block["still_prefix"]
    aspect = "9:16" if short else "16:9"
    jobs = []
    for i, (scene, chunk) in enumerate(zip(scenes, chunks, strict=True)):
        jobs.append(
            {
                "id": f"{i:03d}",
                "filename": f"{prefix}{i:03d}.png",
                "aspect": aspect,
                "who": scene.who,
                "free": scene.who == "empty",
                "shot_type": scene.composition,
                "chunk": chunk,
                "scene": scene.action,
                "prompt": assemble_image_prompt(project, scene, aspect=aspect),
                "camera_motion": scene.camera_motion,
            }
        )
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


def compile_project(
    project: VideoProject,
    *,
    stubs_ok: bool = False,
    root: Path | None = None,
) -> dict[str, str]:
    if not project.story:
        raise ValueError("cannot compile without a story")
    slug = project.slug
    project.metadata = draft_metadata(project)
    fixture = fixture_dict(project)
    chunks = _chunks_for(fixture)
    scenes = list(project.scenes)
    if len(scenes) != len(chunks):
        if not stubs_ok:
            raise ValueError(
                f"scene count {len(scenes)} != narration chunks {len(chunks)}. "
                "Fill scenes 1:1 with channel.compile.chunk_list() output, or "
                "pass stubs_ok=True to write placeholders."
            )
        scenes = stub_scenes(project, chunks)

    fx = fixture_path(slug, root)
    fx.parent.mkdir(parents=True, exist_ok=True)
    fx.write_text(json.dumps(fixture, indent=2) + "\n", encoding="utf-8")
    stills_path(slug, root).write_text(stills_module_source(project, scenes), encoding="utf-8")

    spec = spec_dict(project, root=root)
    sp = spec_path(slug, root)
    sp.parent.mkdir(parents=True, exist_ok=True)
    sp.write_text(json.dumps(spec, indent=2) + "\n", encoding="utf-8")

    written = {
        "fixture": str(fx),
        "stills": str(stills_path(slug, root)),
        "spec": str(sp),
    }

    if CHANNEL.default_short_enabled and project.short:
        sf = fixture_dict(project, short=True)
        short_chunks = _chunks_for(sf)
        short_scenes = list(project.short.scenes)
        if len(short_scenes) != len(short_chunks):
            if not stubs_ok:
                raise ValueError(
                    f"short scenes {len(short_scenes)} != short chunks {len(short_chunks)}"
                )
            short_scenes = stub_scenes(project, short_chunks)
        sfp = short_fixture_path(slug, root)
        sfp.write_text(json.dumps(sf, indent=2) + "\n", encoding="utf-8")
        short_stills_path(slug, root).write_text(
            stills_module_source(project, short_scenes), encoding="utf-8"
        )
        write_jobs(spec, short_scenes, project, short=True, root=root)
        written["short_fixture"] = str(sfp)

    jobs = write_jobs(spec, scenes, project, short=False, root=root)
    written["jobs"] = str(jobs)
    return written
