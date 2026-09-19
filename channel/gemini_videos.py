"""Omni 1.1 Flash clips for documentary jobs.

Named engine video path: Gemini Omni 1.1 Flash (`gemini-omni-1.1-flash`).
Call ``python -m channel videos <JOB_ID>`` after stills exist. Image-to-video
only — each clip is anchored to an ingested still. Assemble prefers
``videos/{still-stem}.mp4`` when present and otherwise holds the still.
Never fall back to Seedance / fal / Flow. Does not run on ``--resume``.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

import httpx

from adapters.image_gen.gemini import mime_for
from adapters.video_gen.gemini_omni import (
    GEMINI_OMNI_ASPECTS,
    GEMINI_OMNI_DEFAULT_RESOLUTION,
    GEMINI_OMNI_VIDEO_MODEL,
    GEMINI_OMNI_VIDEO_PUBLIC_NAME,
    GeminiOmniError,
    GeminiOmniVideoResult,
    clamp_omni_duration,
    generate_video,
    matching_omni_clip,
    omni_motion_prompt,
)
from channel.engine import GEMINI_VIDEO_LOCK
from channel.gemini_images import (
    StillJob,
    find_image_jobs_file,
    load_still_jobs,
)
from channel.gemini_tts import gemini_api_key
from channel.io import load_project
from channel.job import (
    ARTIFACTS,
    JobState,
    ensure_job_tree,
    load_manifest,
    project_path,
    write_manifest,
    write_operator_md,
    write_report,
)
from channel.pauses import load_timestamps

GenerateFn = Callable[..., GeminiOmniVideoResult]

_STILL_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}


class GeminiVideosError(GeminiOmniError):
    """Job-level Omni 1.1 Flash failure."""


def find_ingested_still(dest: Path, job: StillJob) -> Path | None:
    names = [job.filename, Path(job.filename).name]
    if job.generate_filename:
        names.append(job.generate_filename)
    folders = [dest / "images", dest / "images" / "nano_banana"]
    for folder in folders:
        if not folder.is_dir():
            continue
        for name in names:
            candidate = folder / name
            if candidate.is_file() and candidate.stat().st_size > 0:
                return candidate
        stem = Path(job.filename).stem
        for candidate in sorted(folder.glob(f"{stem}.*")):
            if (
                candidate.suffix.lower() in _STILL_SUFFIXES
                and candidate.is_file()
                and candidate.stat().st_size > 0
            ):
                return candidate
    return None


def pause_seconds_for_job(job: StillJob, timestamps: dict[str, Any]) -> float:
    for row in timestamps.get("scenes") or []:
        if int(row.get("index", -1)) == job.index:
            return max(0.1, float(row["end"]) - float(row["start"]))
        filename = str(row.get("filename") or "")
        if filename and filename == job.filename:
            return max(0.1, float(row["end"]) - float(row["start"]))
    if job.end_seconds > job.start_seconds:
        return job.end_seconds - job.start_seconds
    return 5.0


def _qa_ready(dest: Path, job_id: str, artifacts_root: Path | None) -> bool:
    manifest = load_manifest(job_id, root=artifacts_root)
    if manifest.qa.get("ready_to_publish") is True:
        return True
    path = project_path(job_id, root=artifacts_root)
    if not path.is_file():
        return False
    project = load_project(path)
    if project.monetization and project.monetization.ready_to_publish:
        return True
    return False


def generate_job_videos(
    job_id: str,
    *,
    artifacts_root: Path | None = None,
    model: str = GEMINI_OMNI_VIDEO_MODEL,
    resolution: str = GEMINI_OMNI_DEFAULT_RESOLUTION,
    aspect_ratio: str = "",
    force: bool = False,
    only_index: int | None = None,
    limit: int | None = None,
    dry_run: bool = False,
    seconds: float | None = None,
    client: httpx.Client | None = None,
    generate: GenerateFn | None = None,
    api_key: str | None = None,
) -> dict[str, Any]:
    dest = ensure_job_tree(job_id, root=artifacts_root)
    manifest = load_manifest(job_id, root=artifacts_root)
    jobs_file = find_image_jobs_file(dest, manifest.slug)
    jobs = load_still_jobs(jobs_file)
    if not force and not _qa_ready(dest, job_id, artifacts_root):
        raise GeminiVideosError(
            f"not ready_to_publish — do not call Omni 1.1 Flash for {job_id}. "
            "Run qa until originality_score >= 80 and ready_to_publish, or pass --force."
        )
    ts_path = dest / "timestamps.json"
    if not ts_path.is_file():
        raise GeminiVideosError(
            f"no timestamps.json for {job_id} — ingest audio first"
        )
    timestamps = load_timestamps(ts_path)
    aspect = (aspect_ratio or "").strip()
    if not aspect:
        fmt = str(manifest.generation_parameters.get("format") or "")
        aspect = "9:16" if fmt == "short" else "16:9"
    if aspect not in GEMINI_OMNI_ASPECTS:
        raise GeminiVideosError(f"unsupported aspect ratio {aspect!r}")

    key = api_key if api_key is not None else gemini_api_key()
    if not dry_run and generate is None and not key:
        raise GeminiVideosError(
            "GEMINI_API_KEY (or GOOGLE_API_KEY) is missing. "
            "Assemble still holds remain the default. "
            "Do not fall back to Seedance, fal.ai, or Google Flow."
        )
    videos = dest / "videos"
    videos.mkdir(parents=True, exist_ok=True)
    synth = generate or (
        lambda prompt, still, **kwargs: generate_video(
            prompt,
            still,
            api_key=key,
            model=model,
            client=client,
            **kwargs,
        )
    )

    selected = jobs
    if only_index is not None:
        selected = [job for job in jobs if job.index == only_index]
        if not selected:
            raise GeminiVideosError(f"no still job at index {only_index}")
    if limit is not None:
        selected = selected[: max(0, limit)]

    ledger_rows: list[dict[str, Any]] = []
    generated = 0
    skipped = 0
    missing = 0
    cost_usd = 0.0
    for job in selected:
        still_path = find_ingested_still(dest, job)
        if still_path is None:
            missing += 1
            ledger_rows.append(
                {
                    "index": job.index,
                    "filename": job.filename,
                    "status": "missing_still",
                }
            )
            continue
        target = videos / f"{still_path.stem}.mp4"
        if target.is_file() and target.stat().st_size > 0 and not force:
            skipped += 1
            ledger_rows.append(
                {
                    "index": job.index,
                    "filename": target.name,
                    "status": "skipped",
                    "path": str(target),
                    "still": str(still_path),
                }
            )
            continue
        pause = (
            float(seconds)
            if seconds is not None
            else pause_seconds_for_job(job, timestamps)
        )
        duration = clamp_omni_duration(pause)
        prompt = omni_motion_prompt(job.prompt, duration, job.camera_motion)
        if dry_run:
            ledger_rows.append(
                {
                    "index": job.index,
                    "filename": target.name,
                    "status": "dry_run",
                    "duration_seconds": duration,
                    "still": str(still_path),
                    "prompt": prompt,
                }
            )
            continue
        still_bytes = still_path.read_bytes()
        result = synth(
            prompt,
            still_bytes,
            mime=mime_for(still_path),
            aspect_ratio=aspect,
            resolution=resolution,
            duration_seconds=duration,
        )
        target.write_bytes(result.data)
        generated += 1
        cost_usd += float(result.cost_usd or 0.0)
        ledger_rows.append(
            {
                "index": job.index,
                "filename": target.name,
                "status": "generated",
                "path": str(target),
                "still": str(still_path),
                "duration_seconds": duration,
                "cost_usd": result.cost_usd,
                "usage": result.usage,
            }
        )

    ledger = {
        "model": model,
        "public_name": GEMINI_OMNI_VIDEO_PUBLIC_NAME,
        "lock": GEMINI_VIDEO_LOCK,
        "resolution": resolution,
        "aspect_ratio": aspect,
        "generated": generated,
        "skipped": skipped,
        "missing_stills": missing,
        "cost_usd": round(cost_usd, 4),
        "dry_run": dry_run,
        "jobs": ledger_rows,
    }
    ledger_path = videos / "ledger.json"
    if not dry_run:
        ledger_path.write_text(json.dumps(ledger, indent=2) + "\n", encoding="utf-8")
        if generated:
            manifest.models["video"] = model
            if manifest.state in {JobState.images_ingested, JobState.ready}:
                write_manifest(manifest, root=artifacts_root)
            write_report(manifest, root=artifacts_root)
            write_operator_md(manifest, root=artifacts_root)

    return {
        "job_id": job_id,
        "model": model,
        "videos": str(videos),
        "ledger": str(ledger_path),
        "generated": generated,
        "skipped": skipped,
        "missing_stills": missing,
        "cost_usd": round(cost_usd, 4),
        "dry_run": dry_run,
        "jobs": ledger_rows,
    }


__all__ = [
    "GeminiVideosError",
    "find_ingested_still",
    "generate_job_videos",
    "matching_omni_clip",
    "pause_seconds_for_job",
]
