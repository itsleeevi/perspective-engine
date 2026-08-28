"""Operator file ingest: imported voice-over and Google Flow stills."""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

from channel.job import ARTIFACTS, JobState, ensure_job_tree, job_dir, load_manifest, write_manifest, write_operator_md, write_report
from channel.pauses import (
    DEFAULT_PAUSE_MS,
    detect_pauses,
    expected_image_name,
    load_timestamps,
    write_timestamps,
    write_transcript,
)

AUDIO_NAMES = ("voiceover.wav", "voiceover.mp3", "voiceover.m4a", "voiceover.aac")
AUDIO_SUFFIXES = {".wav", ".mp3", ".m4a", ".aac", ".flac", ".ogg"}
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}
# Engine assemble names: 000_00-00-00.png
_ENGINE_STILL = re.compile(r"^\d{3}_\d{2}-\d{2}-\d{2}\.(?:png|jpg|jpeg|webp)$", re.I)
# ZAPI FLOW with serial on: 02_red_cabin.jpg (1-based queue index).
_ZAPI_SERIAL = re.compile(r"^(\d+)[_-]", re.I)
LONG_WIDTH = 3840
LONG_HEIGHT = 2160


def find_voiceover(dest: Path) -> Path | None:
    audio_dir = dest / "audio"
    for name in AUDIO_NAMES:
        path = audio_dir / name
        if path.is_file() and path.stat().st_size > 0:
            return path
    if audio_dir.is_dir():
        candidates = sorted(
            p
            for p in audio_dir.iterdir()
            if p.is_file() and p.suffix.lower() in AUDIO_SUFFIXES and p.stat().st_size > 0
        )
        if candidates:
            return candidates[0]
    return None


def convert_to_wav(src: Path, dest: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if src.resolve() == dest.resolve() and src.suffix.lower() == ".wav":
        return dest
    exe = shutil.which("ffmpeg")
    if not exe:
        if src.suffix.lower() == ".wav":
            if src.resolve() != dest.resolve():
                shutil.copy2(src, dest)
            return dest
        raise RuntimeError("ffmpeg is required to convert imported audio to wav")
    result = subprocess.run(
        [exe, "-y", "-loglevel", "error", "-i", str(src), "-ac", "1", "-ar", "44100", str(dest)],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr[-800:] if result.stderr else "ffmpeg failed")
    return dest


def ingest_audio(
    job_id: str,
    src: Path | None = None,
    *,
    artifacts_root: Path | None = None,
    pause_ms: int = DEFAULT_PAUSE_MS,
) -> dict:
    root = artifacts_root or ARTIFACTS
    dest = ensure_job_tree(job_id, root=root)
    audio_dir = dest / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)
    wav_dest = audio_dir / "voiceover.wav"
    source = Path(src) if src else find_voiceover(dest)
    if source is None:
        raise FileNotFoundError(
            f"no voiceover for {job_id}: pass a file or drop audio/voiceover.wav"
        )
    source = source.resolve()
    if source.suffix.lower() != ".wav" or source != wav_dest.resolve():
        if source.parent == audio_dir and source.name != "voiceover.wav":
            keep = audio_dir / f"voiceover_source{source.suffix.lower()}"
            if source != keep:
                shutil.copy2(source, keep)
        convert_to_wav(source, wav_dest)
    elif source != wav_dest.resolve():
        shutil.copy2(source, wav_dest)
    table = detect_pauses(wav_dest, pause_ms=pause_ms)
    table["audio"] = "audio/voiceover.wav"
    write_timestamps(table, dest / "timestamps.json")
    write_transcript(table, dest / "transcript.txt")
    manifest = load_manifest(job_id, root=root)
    manifest.state = JobState.pauses_detected
    manifest.paths["audio"] = str(wav_dest)
    manifest.paths["timestamps"] = str(dest / "timestamps.json")
    manifest.paths["transcript"] = str(dest / "transcript.txt")
    manifest.notes = [
        f"Detected {table['scene_count']} pause scenes. Fill project.scenes 1:1, then --resume.",
        f"python -m channel generate --resume {job_id}",
    ]
    write_manifest(manifest, root=root)
    write_report(manifest, root=root)
    write_operator_md(manifest, root=root)
    return table


def _write_still_4k(src: Path, dest: Path) -> None:
    """Cover-crop 16:9 and Lanczos-upscale so assemble encodes a 4K long cut."""
    from scripts._media import cover_crop

    cover_crop(src, dest, 16, 9, out_size=(LONG_WIDTH, LONG_HEIGHT))


def _is_long_output(path: Path) -> bool:
    from PIL import Image

    try:
        with Image.open(path) as im:
            return im.size == (LONG_WIDTH, LONG_HEIGHT)
    except OSError:
        return False


def expected_image_names(table: dict) -> list[str]:
    names = []
    for row in table.get("scenes") or []:
        name = str(row.get("filename") or "")
        if not name:
            name = expected_image_name(int(row["index"]), float(row["start"]))
        names.append(name)
    return names


def _pngs(folder: Path) -> list[Path]:
    return sorted(
        p
        for p in folder.iterdir()
        if p.is_file() and p.suffix.lower() in IMAGE_SUFFIXES and p.stat().st_size > 0
    )


def _pick_serial_file(paths: list[Path]) -> Path:
    """Prefer the first download, not OS duplicates like ``02_red_cabin (1).jpg``."""
    clean = [p for p in paths if " (" not in p.stem]
    pool = clean or paths
    return max(pool, key=lambda p: (p.stat().st_mtime, p.stat().st_size))


def map_serial_stills(folder: Path, expected: list[str]) -> list[Path | None]:
    """Map ZAPI ``02_red_cabin.jpg`` onto pause index 1 (1-based queue → 0-based still)."""
    slots: list[Path | None] = [None] * len(expected)
    serials: dict[int, list[Path]] = {}
    for path in _pngs(folder):
        if _ENGINE_STILL.match(path.name):
            continue
        hit = _ZAPI_SERIAL.match(path.name)
        if not hit:
            continue
        serials.setdefault(int(hit.group(1)), []).append(path)
    if not serials:
        return slots
    one_based = 0 not in serials
    for serial, paths in serials.items():
        index = serial - 1 if one_based else serial
        if index < 0 or index >= len(expected):
            continue
        slots[index] = _pick_serial_file(paths)
    return slots


def match_images(folder: Path, expected: list[str]) -> list[Path]:
    by_name = {p.name: p for p in _pngs(folder)}
    exact = [by_name[name] for name in expected if name in by_name]
    if len(exact) == len(expected):
        return exact
    indexed: list[Path] = []
    for i, name in enumerate(expected):
        prefix = f"{i:03d}_"
        hit = by_name.get(name)
        if hit is None:
            matches = [p for p in by_name.values() if p.name.startswith(prefix)]
            hit = matches[0] if matches else None
        if hit is None:
            break
        indexed.append(hit)
    if len(indexed) == len(expected):
        return indexed
    serial = map_serial_stills(folder, expected)
    if all(serial):
        return [p for p in serial if p is not None]
    sorted_pngs = _pngs(folder)
    if len(sorted_pngs) == len(expected):
        return sorted_pngs
    raise FileNotFoundError(
        f"need {len(expected)} stills matching {expected[0] if expected else '000_00-00-00.png'} "
        f"(found {len(sorted_pngs)} in {folder})"
    )


def _resolve_stills(folder: Path, expected: list[str]) -> list[Path | None]:
    """Best still per pause: exact engine name, ``000_`` prefix, or ZAPI serial."""
    by_name = {p.name: p for p in _pngs(folder)}
    slots: list[Path | None] = []
    for i, name in enumerate(expected):
        hit = by_name.get(name)
        if hit is None:
            prefix = f"{i:03d}_"
            matches = [p for p in by_name.values() if p.name.startswith(prefix)]
            hit = matches[0] if matches else None
        slots.append(hit)
    if all(slots):
        return slots
    serial = map_serial_stills(folder, expected)
    return [exact or zapi for exact, zapi in zip(slots, serial, strict=True)]


def stage_images(
    job_id: str,
    src: Path | None = None,
    *,
    artifacts_root: Path | None = None,
) -> dict[str, list[str]]:
    """Copy whatever operator stills map, renamed to ``000_00-00-00.png``.

    Cover-crops 16:9 and Lanczos-upscales to 3840×2160 so the long cut is 4K.
    Does not mark IMAGES_INGESTED. Re-run as ZAPI batches land.
    """
    root = artifacts_root or ARTIFACTS
    dest = job_dir(job_id, root=root)
    ts_path = dest / "timestamps.json"
    if not ts_path.is_file():
        raise FileNotFoundError(f"no timestamps.json in {dest} — ingest audio first")
    table = load_timestamps(ts_path)
    expected = expected_image_names(table)
    folder = Path(src) if src else dest / "images"
    if not folder.is_dir():
        raise FileNotFoundError(f"no image folder at {folder}")
    resolved = _resolve_stills(folder, expected)
    images = dest / "images"
    images.mkdir(parents=True, exist_ok=True)
    copied: list[str] = []
    for name, src_file in zip(expected, resolved, strict=True):
        if src_file is None:
            continue
        target = images / name
        if target.is_file() and _is_long_output(target):
            if src_file.resolve() == target.resolve() or src_file.stat().st_mtime <= target.stat().st_mtime:
                copied.append(name)
                continue
        _write_still_4k(src_file, target)
        copied.append(name)
    already = [name for name in expected if (images / name).is_file()]
    missing = [name for name in expected if name not in already]
    return {"copied": already, "missing": missing, "expected": expected}


def ingest_images(
    job_id: str,
    src: Path | None = None,
    *,
    artifacts_root: Path | None = None,
    require_complete: bool = True,
) -> list[Path]:
    root = artifacts_root or ARTIFACTS
    dest = job_dir(job_id, root=root)
    staged = stage_images(job_id, src, artifacts_root=root)
    expected = staged["expected"]
    images = dest / "images"
    copied = [images / name for name in expected if (images / name).is_file()]
    missing = staged["missing"]
    if missing:
        sample = ", ".join(missing[:5])
        extra = f" (+{len(missing) - 5} more)" if len(missing) > 5 else ""
        msg = (
            f"staged {len(copied)}/{len(expected)} stills into {images} "
            f"(ZAPI 01_set.jpg remaps to 000_00-00-00.png). "
            f"still need {len(missing)} starting at {sample}{extra}"
        )
        if require_complete:
            raise FileNotFoundError(msg)
        return copied
    matched = match_images(images, expected)
    manifest = load_manifest(job_id, root=root)
    manifest.state = JobState.images_ingested
    manifest.paths["images"] = str(images)
    manifest.notes = [
        f"Ingested {len(matched)} stills. Assemble with: python -m channel assemble {job_id}",
    ]
    write_manifest(manifest, root=root)
    write_report(manifest, root=root)
    write_operator_md(manifest, root=root)
    return matched


def images_complete(dest: Path) -> bool:
    ts_path = dest / "timestamps.json"
    if not ts_path.is_file():
        return False
    table = load_timestamps(ts_path)
    expected = expected_image_names(table)
    if not expected:
        return False
    try:
        match_images(dest / "images", expected)
    except FileNotFoundError:
        return False
    return True
