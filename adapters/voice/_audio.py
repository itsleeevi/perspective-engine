"""
Shared local ffmpeg/ffprobe helpers for voice adapters.

Every real voice adapter needs to measure, generate silence for, and
concatenate MP3 segments the same way, so that plumbing lives here once
instead of being copy-pasted per provider.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

SAMPLE_RATE = 44100
BITRATE = "128k"


def ffmpeg() -> str:
    exe = shutil.which("ffmpeg")
    if not exe:
        raise RuntimeError("ffmpeg is required to stitch TTS segments.")
    return exe


def ffprobe() -> str:
    exe = shutil.which("ffprobe")
    if not exe:
        raise RuntimeError("ffprobe is required to measure TTS segments.")
    return exe


def duration_seconds(path: Path) -> float:
    out = subprocess.run(
        [
            ffprobe(),
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=nw=1:nk=1",
            str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    return float(out)


def silence_mp3(path: Path, seconds: float, sample_rate: int = SAMPLE_RATE) -> None:
    subprocess.run(
        [
            ffmpeg(), "-y",
            "-f", "lavfi",
            "-i", f"anullsrc=r={sample_rate}:cl=mono",
            "-t", f"{max(0.05, seconds):.3f}",
            "-c:a", "libmp3lame",
            "-b:a", BITRATE,
            str(path),
        ],
        check=True,
        capture_output=True,
    )


def concat_mp3(
    parts: list[Path], dest: Path, sample_rate: int = SAMPLE_RATE, mono: bool = True
) -> None:
    list_file = dest.parent / "concat.txt"
    list_file.write_text("\n".join(f"file '{p}'" for p in parts))
    cmd = [
        ffmpeg(), "-y",
        "-f", "concat", "-safe", "0",
        "-i", str(list_file),
        "-c:a", "libmp3lame",
        "-b:a", BITRATE,
        "-ar", str(sample_rate),
    ]
    if mono:
        cmd += ["-ac", "1"]
    cmd.append(str(dest))
    subprocess.run(cmd, check=True, capture_output=True)
