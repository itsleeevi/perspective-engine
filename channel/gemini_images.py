"""Nano Banana 2 stills for documentary jobs.

Named engine image path: Gemini 3.1 Flash Image (`gemini-3.1-flash-image`).
Call ``python -m channel images <JOB_ID>`` after compile writes image jobs.
Operator Google Flow ingest still works. Never fall back to fal / OpenAI /
Pollinations. Does not run on ``--resume`` — stills are opt-in and paid.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

import httpx

from adapters.image_gen.gemini import (
    GEMINI_IMAGE_ASPECT,
    GEMINI_IMAGE_MODEL,
    GEMINI_IMAGE_PUBLIC_NAME,
    GEMINI_IMAGE_SIZE,
    GEMINI_IMAGE_SIZES,
    MAX_REFERENCE_IMAGES,
    GeminiImageError,
    GeminiImageResult,
    generate_image,
    mime_for,
)
from channel.engine import GEMINI_IMAGE_LOCK
from channel.gemini_tts import gemini_api_key
from channel.ingest import ingest_images
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
from channel.paths import ROOT

GenerateFn = Callable[..., GeminiImageResult]


class GeminiImagesError(GeminiImageError):
    """Job-level Nano Banana 2 failure."""


@dataclass
class StillJob:
    index: int
    prompt: str
    filename: str
    generate_filename: str
    aspect: str
    reference_paths: list[str] = field(default_factory=list)
    who: str = ""


def _resolve_under(base: Path, rel: str) -> Path | None:
    raw = (rel or "").strip()
    if not raw:
        return None
    path = Path(raw)
    if path.is_file():
        return path
    for root in (base, ROOT):
        candidate = (root / raw).resolve()
        if candidate.is_file():
            return candidate
        candidate = (root / path.name).resolve()
        if candidate.is_file():
            return candidate
    return None


def find_image_jobs_file(dest: Path, slug: str) -> Path:
    spec_path = dest / "fixtures" / "video_specs" / f"{slug}.json"
    if spec_path.is_file():
        spec = json.loads(spec_path.read_text(encoding="utf-8"))
        rel = str(spec.get("image_jobs") or "").strip()
        if rel:
            for candidate in (
                dest / rel,
                ROOT / rel,
                dest / Path(rel).name,
                dest / "fixtures" / Path(rel).name,
            ):
                if candidate.is_file():
                    return candidate
    named = dest / "fixtures" / f"{slug}_v1_image_jobs.json"
    if named.is_file():
        return named
    matches = sorted(
        p
        for p in (dest / "fixtures").glob("*_image_jobs.json")
        if p.is_file() and "_short_" not in p.name and "thumbnail" not in p.name
    )
    if matches:
        return matches[0]
    raise GeminiImagesError(
        f"no image_jobs.json under {dest / 'fixtures'} — compile flow_prompts first"
    )


def load_still_jobs(jobs_file: Path) -> list[StillJob]:
    data = json.loads(jobs_file.read_text(encoding="utf-8"))
    rows = list(data.get("jobs") or [])
    out: list[StillJob] = []
    for i, row in enumerate(rows):
        prompt = str(row.get("prompt") or "").strip()
        filename = str(row.get("filename") or row.get("copy_to") or "").strip()
        if not prompt or not filename:
            continue
        refs = [
            str(p)
            for p in (row.get("reference_image_paths") or [])
            if str(p).strip()
        ]
        out.append(
            StillJob(
                index=i,
                prompt=prompt,
                filename=filename,
                generate_filename=str(row.get("generate_filename") or ""),
                aspect=str(row.get("aspect") or GEMINI_IMAGE_ASPECT),
                reference_paths=refs,
                who=str(row.get("who") or ""),
            )
        )
    if not out:
        raise GeminiImagesError(f"no still jobs in {jobs_file}")
    return out


def load_reference_images(
    rels: list[str],
    *,
    dest: Path,
) -> list[tuple[bytes, str]]:
    loaded: list[tuple[bytes, str]] = []
    seen: set[str] = set()
    for rel in rels:
        path = _resolve_under(dest, rel)
        if path is None:
            path = _resolve_under(ROOT, rel)
        if path is None:
            continue
        key = str(path.resolve())
        if key in seen:
            continue
        seen.add(key)
        data = path.read_bytes()
        if not data:
            continue
        loaded.append((data, mime_for(path)))
        if len(loaded) >= MAX_REFERENCE_IMAGES:
            break
    return loaded


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


def generate_job_images(
    job_id: str,
    *,
    artifacts_root: Path | None = None,
    model: str = GEMINI_IMAGE_MODEL,
    image_size: str = GEMINI_IMAGE_SIZE,
    force: bool = False,
    only_index: int | None = None,
    limit: int | None = None,
    dry_run: bool = False,
    no_ingest: bool = False,
    client: httpx.Client | None = None,
    generate: GenerateFn | None = None,
    api_key: str | None = None,
) -> dict[str, Any]:
    dest = ensure_job_tree(job_id, root=artifacts_root)
    manifest = load_manifest(job_id, root=artifacts_root)
    jobs_file = find_image_jobs_file(dest, manifest.slug)
    jobs = load_still_jobs(jobs_file)
    if not force and not _qa_ready(dest, job_id, artifacts_root):
        raise GeminiImagesError(
            f"not ready_to_publish — do not call Nano Banana 2 for {job_id}. "
            "Run qa until originality_score >= 80 and ready_to_publish, or pass --force."
        )
    if not dry_run and not no_ingest and not (dest / "timestamps.json").is_file():
        raise GeminiImagesError(
            f"no timestamps.json for {job_id} — ingest audio first"
        )
    if image_size not in GEMINI_IMAGE_SIZES:
        raise GeminiImagesError(f"unsupported imageSize {image_size!r}")

    key = api_key if api_key is not None else gemini_api_key()
    if not dry_run and generate is None and not key:
        raise GeminiImagesError(
            "GEMINI_API_KEY (or GOOGLE_API_KEY) is missing. "
            "Operator Google Flow ingest still works. "
            "Do not fall back to fal.ai, OpenAI Images, or Pollinations."
        )
    staging = dest / "images" / "nano_banana"
    staging.mkdir(parents=True, exist_ok=True)
    synth = generate or (
        lambda prompt, **kwargs: generate_image(
            prompt,
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
            raise GeminiImagesError(f"no still job at index {only_index}")
    if limit is not None:
        selected = selected[: max(0, limit)]

    ledger_rows: list[dict[str, Any]] = []
    generated = 0
    skipped = 0
    cost_usd = 0.0
    for job in selected:
        target = staging / job.filename
        if target.is_file() and target.stat().st_size > 0 and not force:
            skipped += 1
            ledger_rows.append(
                {
                    "index": job.index,
                    "filename": job.filename,
                    "status": "skipped",
                    "path": str(target),
                }
            )
            continue
        if dry_run:
            ledger_rows.append(
                {
                    "index": job.index,
                    "filename": job.filename,
                    "status": "dry_run",
                    "refs": job.reference_paths,
                }
            )
            continue
        refs = load_reference_images(job.reference_paths, dest=dest)
        result = synth(
            job.prompt,
            aspect_ratio=job.aspect or GEMINI_IMAGE_ASPECT,
            image_size=image_size,
            reference_images=refs or None,
        )
        target.write_bytes(result.data)
        generated += 1
        cost_usd += float(result.cost_usd)
        ledger_rows.append(
            {
                "index": job.index,
                "filename": job.filename,
                "generate_filename": job.generate_filename,
                "status": "generated",
                "path": str(target),
                "cost_usd": result.cost_usd,
                "usage": result.usage,
                "refs": len(refs),
            }
        )

    ledger = {
        "provider": GEMINI_IMAGE_LOCK["provider"],
        "public_name": GEMINI_IMAGE_PUBLIC_NAME,
        "model": model,
        "image_size": image_size,
        "jobs_file": str(jobs_file),
        "generated": generated,
        "skipped": skipped,
        "dry_run": dry_run,
        "cost_usd": round(cost_usd, 6),
        "stills": ledger_rows,
    }
    (staging / "ledger.json").write_text(
        json.dumps(ledger, indent=2) + "\n", encoding="utf-8"
    )

    ingested = 0
    if not dry_run and not no_ingest and (generated or skipped):
        copied = ingest_images(
            job_id,
            staging,
            artifacts_root=artifacts_root,
            require_complete=False,
        )
        ingested = len(copied)
        manifest = load_manifest(job_id, root=artifacts_root)
        if manifest.state != JobState.images_ingested:
            manifest.notes = [
                f"Nano Banana 2 staged {generated} stills "
                f"({skipped} cached) into {staging}. "
                f"python -m channel ingest-images {job_id} {staging} --partial"
            ]
            write_manifest(manifest, root=artifacts_root)
            write_report(manifest, root=artifacts_root)
            write_operator_md(manifest, root=artifacts_root)

    return {
        "job_id": job_id,
        "model": model,
        "public_name": GEMINI_IMAGE_PUBLIC_NAME,
        "image_size": image_size,
        "jobs": len(jobs),
        "selected": len(selected),
        "generated": generated,
        "skipped": skipped,
        "ingested": ingested,
        "cost_usd": round(cost_usd, 6),
        "dry_run": dry_run,
        "staging": str(staging),
        "ledger": str(staging / "ledger.json"),
        "jobs_file": str(jobs_file),
    }
