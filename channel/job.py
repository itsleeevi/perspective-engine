"""Isolated generation jobs. Parallel Cloud Agents must not share output paths."""

from __future__ import annotations

import json
import secrets
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from channel.engine import (
    IMPORTED_VOICE_LOCK,
    MODEL_LOCK,
    PROMPT_MODULES,
    PROMPT_VERSION,
    RENDER_LOCK,
    VIDEO_ENGINE_VERSION,
    VISUAL_STYLE_VERSION,
)
from channel.modes import ChannelMode, parse_mode
from channel.paths import ROOT
from channel.slug import slugify

ARTIFACTS = ROOT / "artifacts"

JOB_STAGES = (
    "CREATED",
    "TITLE_ANALYZED",
    "RESEARCHED",
    "FACT_CHECKED",
    "STORY_PLANNED",
    "SCRIPTED",
    "SCRIPT_QA_PASSED",
    "WAIT_AUDIO",
    "WAIT_DROP",
    "AUDIO_INGESTED",
    "PAUSES_DETECTED",
    "SCENES_PROMPTED",
    "WAIT_IMAGES",
    "IMAGES_INGESTED",
    "RENDERED",
    "FINAL_QA_PASSED",
    "READY",
)


class JobState(str, Enum):
    created = "CREATED"
    title_analyzed = "TITLE_ANALYZED"
    researched = "RESEARCHED"
    fact_checked = "FACT_CHECKED"
    story_planned = "STORY_PLANNED"
    scripted = "SCRIPTED"
    script_qa_passed = "SCRIPT_QA_PASSED"
    wait_audio = "WAIT_AUDIO"
    wait_drop = "WAIT_DROP"
    audio_ingested = "AUDIO_INGESTED"
    pauses_detected = "PAUSES_DETECTED"
    scenes_prompted = "SCENES_PROMPTED"
    wait_images = "WAIT_IMAGES"
    images_ingested = "IMAGES_INGESTED"
    rendered = "RENDERED"
    final_qa_passed = "FINAL_QA_PASSED"
    ready = "READY"
    blocked = "BLOCKED"
    # Kept so older manifests still load.
    visual_plan_created = "VISUAL_PLAN_CREATED"
    visual_qa_passed = "VISUAL_QA_PASSED"
    assets_generated = "ASSETS_GENERATED"
    audio_generated = "AUDIO_GENERATED"


class GenerationManifest(BaseModel):
    job_id: str
    created_at: str
    channel_mode: str
    title: str
    slug: str
    state: JobState = JobState.created
    engine_version: str = VIDEO_ENGINE_VERSION
    prompt_version: str = PROMPT_VERSION
    visual_style_version: str = VISUAL_STYLE_VERSION
    prompt_module: str = ""
    models: dict[str, str] = Field(default_factory=lambda: dict(MODEL_LOCK))
    render: dict[str, Any] = Field(default_factory=lambda: dict(RENDER_LOCK))
    voice: dict[str, Any] = Field(default_factory=lambda: dict(IMPORTED_VOICE_LOCK))
    generation_parameters: dict[str, Any] = Field(default_factory=dict)
    random_seeds: dict[str, Any] = Field(default_factory=dict)
    research_sources: list[dict[str, str]] = Field(default_factory=list)
    qa: dict[str, Any] = Field(default_factory=dict)
    paths: dict[str, str] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    smoke_test: bool = False
    notes: list[str] = Field(default_factory=list)


def new_job_id(title: str, *, now: datetime | None = None, token: str | None = None) -> str:
    slug = slugify(title)
    stamp = (now or datetime.now(timezone.utc)).strftime("%Y%m%d_%H%M%S")
    suffix = token or secrets.token_hex(3)
    return f"{slug}__{stamp}__{suffix}"


def job_dir(job_id: str, *, root: Path | None = None) -> Path:
    return (root or ARTIFACTS) / job_id


def manifest_path(job_id: str, *, root: Path | None = None) -> Path:
    return job_dir(job_id, root=root) / "manifest.json"


def project_path(job_id: str, *, root: Path | None = None) -> Path:
    return job_dir(job_id, root=root) / "project.json"


def ensure_job_tree(job_id: str, *, root: Path | None = None) -> Path:
    dest = job_dir(job_id, root=root)
    for name in (
        "research",
        "fixtures",
        "fixtures/video_specs",
        "images",
        "drop",
        "audio",
        "thumbnail",
        "short",
        "final",
        "logs",
        "assets/youtube",
    ):
        (dest / name).mkdir(parents=True, exist_ok=True)
    return dest


def write_manifest(manifest: GenerationManifest, *, root: Path | None = None) -> Path:
    dest = manifest_path(manifest.job_id, root=root)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(manifest.model_dump_json(indent=2) + "\n", encoding="utf-8")
    return dest


def load_manifest(job_id: str, *, root: Path | None = None) -> GenerationManifest:
    path = manifest_path(job_id, root=root)
    if not path.is_file():
        raise FileNotFoundError(f"no manifest at {path}")
    return GenerationManifest.model_validate_json(path.read_text(encoding="utf-8"))


def operator_path(job_id: str, *, root: Path | None = None) -> Path:
    return job_dir(job_id, root=root) / "OPERATOR.md"


def write_operator_md(manifest: GenerationManifest, *, root: Path | None = None) -> Path:
    """What a later chat with empty history should do next."""
    dest = operator_path(manifest.job_id, root=root)
    job = manifest.paths.get("job") or str(job_dir(manifest.job_id, root=root))
    script = f"{job}/script.txt"
    audio = f"{job}/audio/voiceover.wav"
    prompts = f"{job}/flow_prompts.txt"
    images = f"{job}/images"
    thumbs = f"{job}/thumbnail_prompts.txt"
    state = manifest.state.value
    blocks = {
        JobState.wait_audio.value: (
            f"# Operator — {manifest.job_id}\n\n"
            f"State: `{state}`\n\n"
            f"1. Copy `{script}` into ElevenLabs (or any TTS). The engine does not call ElevenLabs.\n"
            f"2. Save the file and ingest it:\n\n"
            f"```text\n"
            f".venv/bin/python -m channel ingest-audio {manifest.job_id} /path/to/voiceover.mp3\n"
            f"```\n\n"
            f"Or drop the file at `{audio}` (mp3/m4a/wav also accepted as `voiceover.mp3`) "
            f"then `.venv/bin/python -m channel generate --resume {manifest.job_id}`.\n\n"
            "Do not write scenes yet. Scene cuts come from pauses in this audio.\n"
        ),
        JobState.wait_drop.value: (
            f"# Operator — {manifest.job_id}\n\n"
            f"State: `{state}`\n\n"
            f"Drop-folder cut. Put files in `{job}/drop/`:\n\n"
            f"- narration audio (`.mp3` / `.wav` / `.m4a`)\n"
            f"- stills named with a start clock, e.g. `[00-00]_Hand-drawn_2D_doo.jpg`\n\n"
            f"`[00-13]` starts that picture at 13 seconds. Each still holds until the "
            f"next clock. The last still holds until the audio ends.\n\n"
            f"Then:\n\n"
            f"```text\n"
            f".venv/bin/python -m channel assemble {manifest.job_id}\n"
            f"```\n\n"
            "The engine upscales stills to 3840×2160 and writes a 4K MP4 "
            "without burned captions.\n"
        ),
        JobState.pauses_detected.value: (
            f"# Operator — {manifest.job_id}\n\n"
            f"State: `{state}`\n\n"
            f"Pauses are in `{job}/timestamps.json` and `{job}/transcript.txt`.\n\n"
            "Fill `project.scenes` 1:1 with those timestamps (`MASTER` Stage 3 + "
            "SCENE_BREAKDOWN in the prompt module named in the manifest). Stick-figure "
            "doodle style; named people are recognizable doodle cartoons. Deliver Flow "
            "prompts in batches of 20 and wait for "
            'Reply "next". Then:\n\n'
            f"```text\n"
            f".venv/bin/python -m channel generate --resume {manifest.job_id}\n"
            f"```\n"
        ),
        JobState.wait_images.value: (
            f"# Operator — {manifest.job_id}\n\n"
            f"State: `{state}`\n\n"
            f"Upload `{job}/flow_batches.txt` into ZAPI FLOW (one prompt per line, all stills). "
            f"Or paste `{prompts}` into Google Flow (16:9, one output per prompt, "
            "one blank line between prompts). The engine does not call Flow.\n\n"
            f"Thumbnail prompts: `{thumbs}`.\n\n"
            f"Drop PNGs into `{images}` (names like `000_00-00-00.png`). "
            "ZAPI FLOW ``01_set.jpg`` serials remap on ingest (queue 1 = still 000) "
            "and Lanczos-upscale to 3840×2160 so assemble renders 4K. "
            "Keep serial numbers on; one still per prompt; Character Consistency off.\n\n"
            f"```text\n"
            f".venv/bin/python -m channel ingest-images {manifest.job_id} /path/to/pngs --partial\n"
            f".venv/bin/python -m channel generate --resume {manifest.job_id}\n"
            f"```\n"
        ),
        JobState.images_ingested.value: (
            f"# Operator — {manifest.job_id}\n\n"
            f"State: `{state}`\n\n"
            f"Images are in `{images}`. Assemble the long cut:\n\n"
            f"```text\n"
            f".venv/bin/python -m channel assemble {manifest.job_id}\n"
            f"```\n\n"
            "A Short is a second HITL pass and does not block this long READY.\n"
        ),
    }
    default = (
        f"# Operator — {manifest.job_id}\n\n"
        f"State: `{state}`\n\n"
        f"Channel: `{manifest.channel_mode}`\n"
        f"Title: {manifest.title}\n\n"
        "Follow the **master prompt** (`MASTER`) in the prompt module named in "
        "`manifest.json`. Same staged loop on every channel; DNA is already "
        "customized for this mode. Fill research, story, and narration in "
        "`project.json`. Do not write scenes before the voiceover exists.\n\n"
        f"```text\n"
        f".venv/bin/python -m channel generate --resume {manifest.job_id}\n"
        f"```\n"
    )
    dest.write_text(blocks.get(state, default), encoding="utf-8")
    return dest


def write_report(manifest: GenerationManifest, *, root: Path | None = None) -> Path:
    dest = job_dir(manifest.job_id, root=root) / "report.txt"
    qa = manifest.qa
    lines = [
        f"CHANNEL\t{manifest.channel_mode}",
        f"TITLE\t{manifest.title}",
        f"JOB_ID\t{manifest.job_id}",
        f"STATE\t{manifest.state.value}",
        f"ENGINE_VERSION\t{manifest.engine_version}",
        f"PROMPT_VERSION\t{manifest.prompt_version}",
        f"VISUAL_STYLE_VERSION\t{manifest.visual_style_version}",
        f"TTS\t{manifest.models.get('tts', '')}",
        f"IMAGE\t{manifest.models.get('image', '')}",
        f"SCRIPT_WORD_COUNT\t{qa.get('word_count', '')}",
        f"SCENE_COUNT\t{qa.get('scene_count', '')}",
        f"SOURCE_COUNT\t{qa.get('source_count', '')}",
        f"ORIGINALITY_SCORE\t{qa.get('originality_score', '')}",
        f"READY_TO_PUBLISH\t{qa.get('ready_to_publish', '')}",
        f"PROJECT\t{manifest.paths.get('project', '')}",
        f"SPEC\t{manifest.paths.get('spec', '')}",
        f"FINAL_VIDEO\t{manifest.paths.get('video', '')}",
        f"THUMBNAIL\t{manifest.paths.get('thumbnail', '')}",
        f"SHORT\t{manifest.paths.get('short', '')}",
    ]
    dest.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return dest


def prompt_module_for(mode: ChannelMode | str | None) -> str:
    return PROMPT_MODULES[parse_mode(mode)]


def snapshot_sources(project: Any) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    research = getattr(project, "research", None)
    if research is None:
        return rows
    for ref in list(getattr(research, "seed_sources", []) or []):
        rows.append({"title": ref.title, "url": ref.url, "kind": ref.kind})
    for claim in list(getattr(research, "claims", []) or []):
        for ref in claim.sources:
            rows.append(
                {
                    "claim_id": claim.claim_id,
                    "title": ref.title,
                    "url": ref.url,
                    "kind": ref.kind,
                }
            )
    return rows


def persist_project_sidecars(project: Any, dest: Path) -> None:
    """Job-local bibles and claims. Parallel agents read these, not chat memory."""
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "research").mkdir(parents=True, exist_ok=True)

    def _dump(name: str, payload: Any) -> None:
        (dest / name).write_text(
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    characters = {
        key: person.model_dump()
        for key, person in (getattr(project, "characters", None) or {}).items()
    }
    locations = {
        key: place.model_dump()
        for key, place in (getattr(project, "locations", None) or {}).items()
    }
    _dump("characters.json", characters)
    _dump("locations.json", locations)
    _dump(
        "scenes.json",
        [scene.model_dump() for scene in list(getattr(project, "scenes", None) or [])],
    )
    story = getattr(project, "story", None)
    if story is not None:
        _dump("story.json", story.model_dump())
    research = getattr(project, "research", None)
    if research is not None:
        (dest / "research" / "claims.json").write_text(
            json.dumps(
                [claim.model_dump() for claim in list(research.claims)],
                indent=2,
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
        )
        (dest / "research" / "sources.json").write_text(
            json.dumps(snapshot_sources(project), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
    company: dict[str, Any] = {}
    if getattr(project, "business", None) is not None:
        company["business"] = project.business.model_dump()
    if getattr(project, "takeover", None) is not None:
        company["takeover"] = project.takeover.model_dump()
    if company:
        _dump("company.json", company)
    from channel.qa import narration_of

    spoken = narration_of(project)
    if spoken:
        (dest / "script.txt").write_text(spoken + "\n", encoding="utf-8")


def resolve_project_path(slug_or_job: str, *, artifacts_root: Path | None = None) -> Path:
    """Find project.json for a local slug or an artifacts job id."""
    from channel.paths import project_dir

    local = project_dir(slug_or_job) / "project.json"
    if local.is_file():
        return local
    root = artifacts_root or ARTIFACTS
    exact = root / slug_or_job / "project.json"
    if exact.is_file():
        return exact
    matches = sorted(
        root.glob(f"{slug_or_job}__*/project.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if matches:
        return matches[0]
    loose = [
        path
        for path in root.glob("*/project.json")
        if path.is_file()
    ]
    for path in sorted(loose, key=lambda p: p.stat().st_mtime, reverse=True):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if data.get("slug") == slug_or_job:
            return path
    raise FileNotFoundError(
        f"no project for {slug_or_job!r} under {project_dir(slug_or_job)} "
        f"or {root}/<job_id>/"
    )


def artifact_job_root(project_file: Path, *, artifacts_root: Path | None = None) -> Path | None:
    """If this project lives in an isolated job, return that job directory."""
    resolved = project_file.resolve()
    root = (artifacts_root or ARTIFACTS).resolve()
    try:
        resolved.relative_to(root)
    except ValueError:
        return None
    return resolved.parent


def load_job_file(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"job file {path} must be a JSON object")
    if not data.get("title"):
        raise ValueError(f"job file {path} needs a title")
    return data
