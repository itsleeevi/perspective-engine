"""Canonical generation entry. Isolates each run under artifacts/<job_id>/."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from channel.compile import compile_project
from channel.config import config_for
from channel.engine import IMAGE_FILENAME_RULE, VIDEO_ENGINE_VERSION, image_token_for
from channel.io import load_project, save_project
from channel.job import (
    ARTIFACTS,
    GenerationManifest,
    JobState,
    ensure_job_tree,
    load_job_file,
    load_manifest,
    new_job_id,
    persist_project_sidecars,
    project_path,
    prompt_module_for,
    snapshot_sources,
    write_manifest,
    write_operator_md,
    write_report,
)
from channel.modes import parse_mode
from channel.qa import narration_of, run_full_qa, word_count
from channel.research import seed_research
from channel.schema import (
    BusinessContext,
    Chapter,
    ResearchPack,
    Scene,
    ScenePurpose,
    StoryPlan,
    TakeoverContext,
    VideoProject,
)
from channel.slug import slugify
from channel.title import analyze_title

NEXT_STEPS = (
    "Follow MASTER in the prompt module named in the manifest (channel/master_prompt.py). Same staged loop; DNA is already per-channel.",
    "Fill research.claims from primary sources. Do not invent numbers or quotes.",
    "python -m channel generate --resume {job_id}   # after research/story/narration exist",
    "python -m channel qa is also available on --resume once the project is filled.",
    "After SCRIPT_QA_PASSED: copy script.txt into ElevenLabs. Then ingest-audio. Do not write scenes yet.",
    "Do not emit flow_prompts until originality_score >= 80 and ready_to_publish.",
    "Paste flow_prompts.txt into Google Flow. Then ingest-images. Then assemble.",
    IMAGE_FILENAME_RULE,
    "Assemble: python -m channel assemble {job_id}  (Shorts are a second HITL pass and do not block long READY)",
    "DO NOT MODIFY THE VIDEO ENGINE, CHANNEL PROMPTS, GLOBAL STYLE, MODEL CONFIGURATION, OR QA THRESHOLDS DURING A NORMAL VIDEO GENERATION TASK.",
)


def _duration_seconds(raw: int | float | None, minutes: float | None, default: int) -> int:
    if raw:
        return int(raw)
    if minutes:
        return int(round(float(minutes) * 60))
    return default


def _new_project(
    title: str,
    *,
    channel: str,
    instructions: str = "",
    duration: int | None = None,
    skip_seed: bool = False,
) -> VideoProject:
    mode = parse_mode(channel)
    cfg = config_for(mode)
    analysis = analyze_title(
        title,
        special_instructions=instructions,
        target_duration_seconds=duration or cfg.target_duration_seconds,
        channel_mode=mode,
    )
    pack = ResearchPack(subject=analysis.subject, target=analysis.target)
    if not skip_seed:
        pack = seed_research(analysis)
    business = None
    takeover = None
    if mode.value == "behind_the_business":
        business = BusinessContext(
            company=analysis.company or analysis.subject,
            industry=analysis.industry,
            business_question=analysis.business_question or analysis.core_question,
            apparent_business=analysis.apparent_business,
            potential_hidden_engine=analysis.potential_hidden_engine,
            customer=analysis.customer,
            likely_revenue_streams=list(analysis.likely_revenue_streams),
        )
    elif mode.value == "how_they_took_over":
        takeover = TakeoverContext(
            subject=analysis.subject,
            arena=analysis.arena,
            starting_position=analysis.starting_position,
            current_position=analysis.dominant_position,
        )
    return VideoProject(
        title=analysis.title,
        slug=slugify(analysis.title),
        channel_mode=mode,
        analysis=analysis,
        business=business,
        takeover=takeover,
        research=pack,
        special_instructions=analysis.special_instructions,
    )


def _smoke_story(project: VideoProject) -> None:
    cfg = config_for(project.channel_mode)
    payoff = (
        project.analysis.core_question.split("?")[0] + " is the title answer."
    )
    hook = (
        f"{project.analysis.subject} looks simple from the outside. "
        f"The real question is {project.analysis.core_question} "
        "The gap between the start and the end is the story."
    )
    body = (
        "Then something changed. Competitors noticed. "
        "The reason to keep watching is the next decision, not a date list. "
    )
    project.story = StoryPlan(
        hook=hook,
        central_question=project.analysis.core_question,
        initial_assumption="the obvious public story",
        first_reveal="the first sourced surprise",
        major_contradiction="the public story is incomplete",
        turning_point="the decision that compounded",
        final_answer=payoff,
        title_payoff=payoff,
        next_video_bridge="A related title is waiting if this one holds.",
        signature_prop="the returning object",
        chapters=[
            Chapter(name="The Gap", purpose=ScenePurpose.hook, narration=body),
            Chapter(name="The Bet", purpose=ScenePurpose.question, narration=body),
            Chapter(name="The Turn", purpose=ScenePurpose.reveal, narration=body + " " + payoff),
        ],
    )
    project.scenes = [
        Scene(
            scene_id="scene_000",
            narration=hook,
            purpose=ScenePurpose.hook,
            visual_type="ORIGIN_SCENE",
            action="Wide empty workshop, no logos, no readable type.",
            composition="wide shot",
            who="empty",
        )
    ]
    project.special_instructions = (
        project.special_instructions + f" smoke-test word budget ignored ({cfg.name})"
    ).strip()


def _refresh_qa(manifest: GenerationManifest, project: VideoProject) -> None:
    text = narration_of(project)
    sourced = sum(1 for c in project.research.claims if c.sources)
    orig = project.originality.originality_score if project.originality else None
    ready = project.monetization.ready_to_publish if project.monetization else False
    manifest.qa = {
        "word_count": word_count(text) if text else 0,
        "scene_count": len(project.scenes),
        "source_count": sourced + len(project.research.seed_sources),
        "originality_score": orig,
        "ready_to_publish": ready,
        "factcheck_ok": project.factcheck.ok if project.factcheck else False,
    }
    manifest.research_sources = snapshot_sources(project)


def start_job(
    *,
    title: str,
    channel: str,
    instructions: str = "",
    duration: int | None = None,
    duration_minutes: float | None = None,
    skip_seed: bool = False,
    smoke_test: bool = False,
    job_id: str | None = None,
    artifacts_root: Path | None = None,
) -> GenerationManifest:
    mode = parse_mode(channel)
    cfg = config_for(mode)
    seconds = _duration_seconds(duration, duration_minutes, cfg.target_duration_seconds)
    jid = job_id or new_job_id(title)
    root = artifacts_root or ARTIFACTS
    dest = ensure_job_tree(jid, root=root)
    project = _new_project(
        title,
        channel=channel,
        instructions=instructions,
        duration=seconds,
        skip_seed=skip_seed or smoke_test,
    )
    state = JobState.title_analyzed
    if smoke_test:
        _smoke_story(project)
        state = JobState.visual_plan_created
    save_project(project, dest / "project.json")
    persist_project_sidecars(project, dest)
    (dest / "research" / "seed.json").write_text(
        project.research.model_dump_json(indent=2) + "\n", encoding="utf-8"
    )
    manifest = GenerationManifest(
        job_id=jid,
        created_at=datetime.now(timezone.utc).isoformat(),
        channel_mode=mode.value,
        title=project.title,
        slug=project.slug,
        state=state,
        prompt_module=prompt_module_for(mode),
        generation_parameters={
            "target_duration_seconds": seconds,
            "kokoro_speed": cfg.kokoro_speed,
            "narration_word_min": cfg.narration_word_min,
            "narration_word_max": cfg.narration_word_max,
            "visual_style": cfg.visual_style[:160],
            "engine_version": VIDEO_ENGINE_VERSION,
        },
        smoke_test=smoke_test,
        paths={
            "job": str(dest),
            "project": str(dest / "project.json"),
            "manifest": str(dest / "manifest.json"),
        },
        notes=[step.format(job_id=jid) for step in NEXT_STEPS],
    )
    if smoke_test:
        written = compile_project(
            project,
            stubs_ok=True,
            root=dest,
            image_token=image_token_for(project.slug, jid),
        )
        save_project(project, dest / "project.json")
        persist_project_sidecars(project, dest)
        manifest.paths.update(written)
        manifest.paths["video"] = str(dest / "final" / f"{project.slug}.mp4")
        manifest.paths["thumbnail"] = str(dest / "thumbnail" / f"{project.slug}.jpg")
        manifest.paths["short"] = str(dest / "short" / f"{project.slug}_short.mp4")
        manifest.state = JobState.visual_qa_passed
        manifest.notes = [
            "smoke-test: no operator audio, no Google Flow, no network spend after the optional seed skip",
            *[step.format(job_id=jid) for step in NEXT_STEPS],
        ]
    _refresh_qa(manifest, project)
    write_manifest(manifest, root=root)
    write_report(manifest, root=root)
    write_operator_md(manifest, root=root)
    return manifest


def _persist(manifest: GenerationManifest, project: VideoProject, dest: Path, *, root: Path) -> None:
    save_project(project, dest / "project.json")
    persist_project_sidecars(project, dest)
    _refresh_qa(manifest, project)
    write_manifest(manifest, root=root)
    write_report(manifest, root=root)
    write_operator_md(manifest, root=root)
    manifest.paths["operator"] = str(dest / "OPERATOR.md")


def resume_job(
    job_id: str,
    *,
    artifacts_root: Path | None = None,
    force: bool = False,
    stubs: bool = False,
) -> GenerationManifest:
    from channel.ingest import find_voiceover, images_complete, ingest_audio

    root = artifacts_root or ARTIFACTS
    manifest = load_manifest(job_id, root=root)
    path = project_path(job_id, root=root)
    if not path.is_file():
        raise FileNotFoundError(f"no project at {path}")
    project = load_project(path)
    dest = ensure_job_tree(job_id, root=root)
    persist_project_sidecars(project, dest)

    if manifest.smoke_test:
        written = compile_project(
            project,
            stubs_ok=True,
            root=dest,
            image_token=image_token_for(project.slug, job_id),
        )
        manifest.paths.update(written)
        manifest.state = JobState.wait_audio
        _persist(manifest, project, dest, root=root)
        return manifest

    if project.research.claims:
        report, _scores, originality, monetization = run_full_qa(project)
        save_project(project, path)
        if originality:
            manifest.qa["originality_score"] = originality.originality_score
        if monetization:
            manifest.qa["ready_to_publish"] = monetization.ready_to_publish
        if not report.ok:
            manifest.warnings.append("factcheck not ok")
            manifest.state = JobState.blocked
            _persist(manifest, project, dest, root=root)
            return manifest
        if monetization and not monetization.ready_to_publish and not force:
            manifest.warnings.append("not ready_to_publish — do not emit flow_prompts")
            manifest.state = JobState.blocked
            _persist(manifest, project, dest, root=root)
            return manifest

    if not project.story:
        manifest.state = JobState.researched if project.research.claims else JobState.title_analyzed
        _persist(manifest, project, dest, root=root)
        return manifest

    spoken = narration_of(project)
    if not spoken.strip():
        manifest.state = JobState.story_planned
        _persist(manifest, project, dest, root=root)
        return manifest

    written = compile_project(
        project,
        stubs_ok=stubs,
        root=dest,
        image_token=image_token_for(project.slug, job_id),
        stage="script",
    )
    manifest.paths.update(written)
    manifest.state = JobState.script_qa_passed

    ts_path = dest / "timestamps.json"
    if not ts_path.is_file() and find_voiceover(dest) is not None:
        ingest_audio(job_id, artifacts_root=root)
        manifest = load_manifest(job_id, root=root)
        project = load_project(path)
        ts_path = dest / "timestamps.json"

    if not ts_path.is_file():
        if project.scenes and not stubs:
            manifest.warnings.append(
                "scenes before audio — ingest the voiceover first; pause table owns scene cuts"
            )
        manifest.state = JobState.wait_audio
        manifest.notes = [
            f"Copy {dest / 'script.txt'} into ElevenLabs, then: "
            f"python -m channel ingest-audio {job_id} /path/to/voiceover.mp3",
            *[step.format(job_id=job_id) for step in NEXT_STEPS],
        ]
        _persist(manifest, project, dest, root=root)
        return manifest

    from channel.pauses import load_timestamps

    table = load_timestamps(ts_path)
    n = len(table.get("scenes") or [])
    manifest.paths["timestamps"] = str(ts_path)
    manifest.paths["transcript"] = str(dest / "transcript.txt")
    ready = bool(project.monetization and project.monetization.ready_to_publish) or force or stubs

    if len(project.scenes) != n:
        manifest.state = JobState.pauses_detected
        manifest.notes = [
            f"{n} pause scenes in timestamps.json. Fill project.scenes 1:1, then --resume.",
        ]
        _persist(manifest, project, dest, root=root)
        return manifest

    if not ready:
        manifest.state = JobState.blocked
        manifest.warnings.append("not ready_to_publish — do not emit flow_prompts")
        _persist(manifest, project, dest, root=root)
        return manifest

    written = compile_project(
        project,
        stubs_ok=stubs,
        root=dest,
        image_token=image_token_for(project.slug, job_id),
        timestamps=table,
    )
    manifest.paths.update(written)
    manifest.state = JobState.wait_images
    if images_complete(dest):
        manifest.state = JobState.images_ingested
        manifest.notes = [
            f"Images ready. Assemble: python -m channel assemble {job_id}",
        ]
    else:
        manifest.notes = [
            f"Paste {dest / 'flow_prompts.txt'} into Google Flow, then: "
            f"python -m channel ingest-images {job_id} /path/to/pngs",
        ]
    _persist(manifest, project, dest, root=root)
    return manifest


def run_generate(args: Any) -> int:
    root = Path(args.artifacts) if getattr(args, "artifacts", None) else ARTIFACTS
    if args.resume:
        manifest = resume_job(
            args.resume,
            artifacts_root=root,
            force=bool(getattr(args, "force", False)),
            stubs=bool(getattr(args, "stubs", False)),
        )
    else:
        title = args.title
        channel = args.channel
        minutes = getattr(args, "duration_minutes", None)
        if args.job:
            data = load_job_file(Path(args.job))
            title = title or data["title"]
            channel = channel or data.get("channel") or data.get("channelMode") or data.get("channel_mode")
            minutes = minutes or data.get("targetDurationMinutes")
        if not title or not channel:
            raise SystemExit("generate needs --channel and --title, or --job, or --resume")
        manifest = start_job(
            title=title,
            channel=channel,
            instructions=getattr(args, "instructions", "") or "",
            duration=getattr(args, "duration", None),
            duration_minutes=minutes,
            skip_seed=bool(getattr(args, "skip_seed", False)),
            smoke_test=bool(getattr(args, "smoke_test", False)),
            job_id=getattr(args, "job_id", None) or None,
            artifacts_root=root,
        )
    print(json.dumps(manifest.model_dump(), indent=2))
    print(f"job_id: {manifest.job_id}")
    print(f"job_dir: {manifest.paths.get('job')}")
    print(f"project: {manifest.paths.get('project')}")
    if manifest.paths.get("spec"):
        print(f"spec: {manifest.paths['spec']}")
    print(f"report: {root / manifest.job_id / 'report.txt'}")
    print(f"state: {manifest.state.value}")
    return 0 if manifest.state is not JobState.blocked else 1
