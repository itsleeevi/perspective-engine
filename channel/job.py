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
    KOKORO_LOCK,
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
    "VISUAL_PLAN_CREATED",
    "VISUAL_QA_PASSED",
    "ASSETS_GENERATED",
    "AUDIO_GENERATED",
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
    visual_plan_created = "VISUAL_PLAN_CREATED"
    visual_qa_passed = "VISUAL_QA_PASSED"
    assets_generated = "ASSETS_GENERATED"
    audio_generated = "AUDIO_GENERATED"
    rendered = "RENDERED"
    final_qa_passed = "FINAL_QA_PASSED"
    ready = "READY"
    blocked = "BLOCKED"


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
    voice: dict[str, Any] = Field(default_factory=lambda: dict(KOKORO_LOCK))
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
