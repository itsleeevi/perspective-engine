"""Drop-folder cut: timestamped stills + narration audio → 4K MP4.

Operator puts files in ``artifacts/<JOB_ID>/drop/``:

- narration: any ``.mp3`` / ``.wav`` / ``.m4a`` / ``.aac`` / ``.flac`` / ``.ogg``
- stills named with a start clock, e.g. ``[00-00]_Hand-drawn_2D_doo.jpg``

Cuts come from those clocks, not from pause detection. Each still holds until
the next timestamp. The last still holds until the audio ends. Assemble does
not burn captions.
"""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from channel.job import GenerationManifest

from channel.engine import VIDEO_ENGINE_VERSION
from channel.ingest import AUDIO_SUFFIXES, IMAGE_SUFFIXES, convert_to_wav
from channel.job import (
    ARTIFACTS,
    JobState,
    ensure_job_tree,
    job_dir,
    load_manifest,
    write_manifest,
    write_operator_md,
    write_report,
)
from channel.pauses import (
    FPS,
    PauseScene,
    audio_duration_seconds,
    expected_image_name,
    timestamp_table,
    write_timestamps,
)
from channel.slug import slugify

# [01-12-05] hours-minutes-seconds, or [01:12:05]
_BRACKET_HMS = re.compile(r"\[(\d{1,2})[-:](\d{2})[-:](\d{2})\]")
# [00-13] or [00:13] minutes-seconds (operator Flow exports)
_BRACKET_MS = re.compile(r"\[(\d{1,3})[-:](\d{2})\]")
# Engine assemble name: 000_00-00-04.png (index_MM-SS-FF)
_ENGINE_STILL = re.compile(
    r"^\d{3}_(\d{2})-(\d{2})-(\d{2})\.(?:png|jpg|jpeg|webp)$", re.I
)

DROP_README = """# Drop folder

Put the narration audio and the stills in this folder, then assemble.

## Audio

Any one of: `.mp3` `.wav` `.m4a` `.aac` `.flac` `.ogg`

Name it `voiceover.mp3` if you want, or leave the original name.

## Stills

Name each still with the **start time** in brackets. Minutes-seconds.

```text
[00-00]_Hand-drawn_2D_doo.jpg
[00-03]_Hand-drawn_2D_doo.jpg
[00-13]_Hand-drawn_2D_doo.jpg
[01-01]_Hand-drawn_2D_doo.jpg
```

`[00-13]` means this picture starts at 0 minutes 13 seconds. It holds until
the next still's clock. The last still holds until the audio ends.

Do not put a company or person name in the filename.

## Assemble

```text
.venv/bin/python -m channel assemble {job_id}
```

The engine Lanczos-upscales stills to 3840×2160, muxes the voice-over, and
writes a YouTube-ready 4K MP4 **without burned captions**.
"""


def parse_still_start(name: str) -> float | None:
    """Seconds from ``[00-13]_….jpg`` or ``000_00-00-04.png``. None if no clock."""
    stem_name = Path(name).name
    hit = _BRACKET_HMS.search(stem_name)
    if hit:
        hours, minutes, seconds = (int(hit.group(1)), int(hit.group(2)), int(hit.group(3)))
        return float(hours * 3600 + minutes * 60 + seconds)
    hit = _BRACKET_MS.search(stem_name)
    if hit:
        minutes, seconds = int(hit.group(1)), int(hit.group(2))
        return float(minutes * 60 + seconds)
    hit = _ENGINE_STILL.match(stem_name)
    if hit:
        minutes, seconds, frames = (int(hit.group(1)), int(hit.group(2)), int(hit.group(3)))
        return minutes * 60 + seconds + frames / float(FPS)
    return None


def _image_files(folder: Path) -> list[Path]:
    if not folder.is_dir():
        return []
    return sorted(
        p
        for p in folder.iterdir()
        if p.is_file() and p.suffix.lower() in IMAGE_SUFFIXES and p.stat().st_size > 0
    )


def list_timestamped_stills(folder: Path) -> list[tuple[float, Path]]:
    """Unique start times, sorted. Duplicate clocks keep the cleanest filename."""
    by_start: dict[float, list[Path]] = {}
    for path in _image_files(folder):
        start = parse_still_start(path.name)
        if start is None:
            continue
        by_start.setdefault(start, []).append(path)
    rows: list[tuple[float, Path]] = []
    for start, paths in sorted(by_start.items()):
        clean = [p for p in paths if " (" not in p.stem]
        pool = clean or paths
        chosen = max(pool, key=lambda p: (p.stat().st_mtime, p.stat().st_size))
        rows.append((start, chosen))
    return rows


def find_drop_audio(folder: Path) -> Path | None:
    if not folder.is_dir():
        return None
    preferred: list[Path] = []
    others: list[Path] = []
    for path in folder.iterdir():
        if not path.is_file() or path.suffix.lower() not in AUDIO_SUFFIXES:
            continue
        if path.stat().st_size <= 0:
            continue
        if path.stem.lower() in {"voiceover", "narration", "audio", "vo"}:
            preferred.append(path)
        else:
            others.append(path)
    pool = preferred or others
    if not pool:
        return None
    return sorted(pool, key=lambda p: p.name.lower())[0]


def drop_dir(job: Path) -> Path:
    return job / "drop"


def drop_has_payload(job: Path) -> bool:
    folder = drop_dir(job)
    return bool(list_timestamped_stills(folder) and find_drop_audio(folder))


def timestamps_from_stills(
    stills: list[tuple[float, Path]],
    duration: float,
) -> tuple[list[PauseScene], list[Path]]:
    if not stills:
        raise ValueError("no timestamped stills")
    if duration <= 0:
        raise ValueError("audio duration must be positive")
    usable = [(start, path) for start, path in stills if start < duration - 1e-6]
    if not usable:
        raise ValueError(
            f"every still starts at or after the audio end ({duration:.3f}s)"
        )
    starts = [start for start, _path in usable]
    paths = [path for _start, path in usable]
    if starts[0] > 0:
        starts[0] = 0.0
    scenes: list[PauseScene] = []
    used: list[Path] = []
    for i, start in enumerate(starts):
        end = starts[i + 1] if i + 1 < len(starts) else float(duration)
        if end <= start:
            continue
        scenes.append(
            PauseScene(
                index=len(scenes),
                start=round(float(start), 3),
                end=round(float(end), 3),
                text="",
            )
        )
        used.append(paths[i])
    if not scenes:
        raise ValueError("timestamped stills produced no scenes")
    scenes[-1] = PauseScene(
        index=scenes[-1].index,
        start=scenes[-1].start,
        end=round(float(duration), 3),
        text="",
    )
    return scenes, used


def _write_still_4k(src: Path, dest: Path) -> None:
    from scripts._media import cover_crop

    cover_crop(src, dest, 16, 9, out_size=(3840, 2160))


def _write_drop_spec(
    dest: Path,
    *,
    title: str,
    slug: str,
    channel_mode: str,
) -> Path:
    specs = dest / "fixtures" / "video_specs"
    specs.mkdir(parents=True, exist_ok=True)
    path = specs / f"{slug}.json"
    spec = {
        "engine": "channel",
        "engine_version": VIDEO_ENGINE_VERSION,
        "channel_mode": channel_mode,
        "topic": title,
        "fixture": slug,
        "voice": "imported",
        "imported_audio": "audio/voiceover.wav",
        "timestamps": "timestamps.json",
        "stills_dir": "images",
        "output": f"final/{slug}.mp4",
        "burn_captions": False,
        "cut_source": "drop_filename_timestamps",
    }
    path.write_text(json.dumps(spec, indent=2) + "\n", encoding="utf-8")
    return path


def write_drop_readme(folder: Path, job_id: str) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / "README.md"
    path.write_text(DROP_README.format(job_id=job_id), encoding="utf-8")
    return path


def copy_into_drop(
    folder: Path,
    *,
    images: Path | None = None,
    audio: Path | None = None,
) -> dict[str, list[str]]:
    """Copy operator files into the drop folder. Accepts a file or a directory."""
    folder.mkdir(parents=True, exist_ok=True)
    copied_images: list[str] = []
    copied_audio: list[str] = []
    if images is not None:
        src = Path(images)
        files = [src] if src.is_file() else _image_files(src)
        for path in files:
            target = folder / path.name
            if path.resolve() != target.resolve():
                shutil.copy2(path, target)
            copied_images.append(target.name)
    if audio is not None:
        src = Path(audio)
        if src.is_dir():
            found = find_drop_audio(src)
            if found is None:
                raise FileNotFoundError(f"no audio file in {src}")
            src = found
        if not src.is_file():
            raise FileNotFoundError(f"no audio file at {src}")
        target = folder / src.name
        if src.resolve() != target.resolve():
            shutil.copy2(src, target)
        copied_audio.append(target.name)
    return {"images": copied_images, "audio": copied_audio}


def start_drop_job(
    *,
    title: str,
    channel: str,
    job_id: str | None = None,
    artifacts_root: Path | None = None,
) -> GenerationManifest:
    from channel.generate import start_job

    root = artifacts_root or ARTIFACTS
    manifest = start_job(
        title=title,
        channel=channel,
        skip_seed=True,
        job_id=job_id,
        artifacts_root=root,
    )
    dest = ensure_job_tree(manifest.job_id, root=root)
    write_drop_readme(drop_dir(dest), manifest.job_id)
    manifest = load_manifest(manifest.job_id, root=root)
    manifest.state = JobState.wait_drop
    manifest.paths["drop"] = str(drop_dir(dest))
    manifest.notes = [
        f"Put timestamped stills ([00-00]_….jpg) and narration audio in {drop_dir(dest)}",
        f"Then: python -m channel assemble {manifest.job_id}",
        "Drop-folder cuts assemble without burned captions.",
    ]
    write_manifest(manifest, root=root)
    write_report(manifest, root=root)
    write_operator_md(manifest, root=root)
    return manifest


def ingest_drop(
    job_id: str,
    *,
    artifacts_root: Path | None = None,
    images: Path | None = None,
    audio: Path | None = None,
) -> dict:
    """Import drop-folder audio + stills, upscale to 4K, write timestamps from filenames."""
    root = artifacts_root or ARTIFACTS
    dest = ensure_job_tree(job_id, root=root)
    folder = drop_dir(dest)
    if images is not None or audio is not None:
        copy_into_drop(folder, images=images, audio=audio)
    stills = list_timestamped_stills(folder)
    source_audio = find_drop_audio(folder)
    if source_audio is None:
        raise FileNotFoundError(
            f"no narration audio in {folder} — drop a .mp3/.wav/.m4a there"
        )
    if not stills:
        raise FileNotFoundError(
            f"no timestamped stills in {folder} — names must look like "
            f"[00-00]_Hand-drawn_2D_doo.jpg"
        )
    wav_dest = dest / "audio" / "voiceover.wav"
    convert_to_wav(source_audio, wav_dest)
    duration = audio_duration_seconds(wav_dest)
    scenes, sources = timestamps_from_stills(stills, duration)
    table = timestamp_table(
        scenes, duration, pause_ms=0, audio="audio/voiceover.wav"
    )
    table["cut_source"] = "drop_filename_timestamps"
    images_dir = dest / "images"
    images_dir.mkdir(parents=True, exist_ok=True)
    copied: list[str] = []
    for scene, src in zip(scenes, sources, strict=True):
        name = expected_image_name(scene.index, scene.start)
        _write_still_4k(src, images_dir / name)
        copied.append(name)
        scene_row = table["scenes"][scene.index]
        scene_row["filename"] = name
        scene_row["source"] = src.name
    write_timestamps(table, dest / "timestamps.json")
    manifest = load_manifest(job_id, root=root)
    spec = _write_drop_spec(
        dest,
        title=manifest.title,
        slug=manifest.slug or slugify(manifest.title),
        channel_mode=manifest.channel_mode,
    )
    manifest.state = JobState.images_ingested
    manifest.paths["audio"] = str(wav_dest)
    manifest.paths["timestamps"] = str(dest / "timestamps.json")
    manifest.paths["images"] = str(images_dir)
    manifest.paths["spec"] = str(spec)
    manifest.paths["drop"] = str(folder)
    manifest.notes = [
        f"Ingested {len(copied)} timestamped stills (4K) + audio from {folder}",
        f"Assemble without burned captions: python -m channel assemble {job_id}",
    ]
    write_manifest(manifest, root=root)
    write_report(manifest, root=root)
    write_operator_md(manifest, root=root)
    return table


def assemble_drop(
    job_id: str,
    *,
    artifacts_root: Path | None = None,
    images: Path | None = None,
    audio: Path | None = None,
) -> Path:
    """Upscale drop-folder stills to 4K and mux narration. No burned captions."""
    from channel.assemble_hitl import assemble_hitl

    ingest_drop(
        job_id,
        artifacts_root=artifacts_root,
        images=images,
        audio=audio,
    )
    return assemble_hitl(
        job_id, artifacts_root=artifacts_root, burn_captions=False
    )
