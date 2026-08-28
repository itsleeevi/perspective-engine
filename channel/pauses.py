"""Cut scenes from pauses in an imported voice-over.

Voice first, pictures second. A scene boundary is a real gap in the audio,
not a word-count estimate.
"""

from __future__ import annotations

import json
import re
import shutil
import struct
import subprocess
import wave
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DEFAULT_PAUSE_MS = 280
MIN_SCENE_SECONDS = 0.5
NEAR_MS = 50
FPS = 30


@dataclass(frozen=True)
class Word:
    text: str
    start: float
    end: float


@dataclass(frozen=True)
class PauseScene:
    index: int
    start: float
    end: float
    text: str

    @property
    def duration(self) -> float:
        return max(0.0, self.end - self.start)

    @property
    def timestamp(self) -> str:
        return format_mmss(self.start)

    @property
    def filename(self) -> str:
        return expected_image_name(self.index, self.start)


def format_mmss(seconds: float) -> str:
    total = max(0, int(seconds))
    minutes, secs = divmod(total, 60)
    return f"{minutes:02d}:{secs:02d}"


def format_mmssff(seconds: float, *, fps: int = FPS) -> str:
    total = max(0.0, float(seconds))
    minutes = int(total // 60)
    remainder = total - minutes * 60
    secs = int(remainder)
    frames = int(round((remainder - secs) * fps))
    if frames >= fps:
        secs += 1
        frames = 0
    if secs >= 60:
        minutes += 1
        secs = 0
    return f"{minutes:02d}-{secs:02d}-{frames:02d}"


def expected_image_name(index: int, start_seconds: float, *, fps: int = FPS) -> str:
    return f"{index:03d}_{format_mmssff(start_seconds, fps=fps)}.png"


def _unique_splits(points: list[float], *, near: float = NEAR_MS / 1000.0) -> list[float]:
    ordered = sorted(max(0.0, p) for p in points)
    out: list[float] = []
    for point in ordered:
        if not out or point - out[-1] >= near:
            out.append(point)
        else:
            out[-1] = (out[-1] + point) / 2.0
    return out


def scenes_from_splits(
    splits: list[float],
    duration: float,
    words: list[Word] | None = None,
    *,
    min_scene: float = MIN_SCENE_SECONDS,
) -> list[PauseScene]:
    ends = _unique_splits([*splits, float(duration)])
    if not ends or ends[0] > 0.05:
        ends = [0.0, *ends]
    else:
        ends[0] = 0.0
    if ends[-1] < duration - 0.01:
        ends.append(duration)
    else:
        ends[-1] = duration
    raw: list[tuple[float, float]] = []
    for start, end in zip(ends, ends[1:]):
        if end - start <= 1e-6:
            continue
        raw.append((start, end))
    merged: list[tuple[float, float]] = []
    for start, end in raw:
        if merged and (end - start) < min_scene:
            prev_start, _prev_end = merged[-1]
            merged[-1] = (prev_start, end)
        else:
            merged.append((start, end))
    scenes: list[PauseScene] = []
    for i, (start, end) in enumerate(merged):
        text = ""
        if words:
            parts = [w.text for w in words if w.start < end - 1e-6 and w.end > start + 1e-6]
            text = " ".join(parts).strip()
        scenes.append(PauseScene(index=i, start=round(start, 3), end=round(end, 3), text=text))
    return scenes


def scenes_from_words(
    words: list[Word],
    duration: float,
    *,
    pause_ms: int = DEFAULT_PAUSE_MS,
    min_scene: float = MIN_SCENE_SECONDS,
) -> list[PauseScene]:
    pause = pause_ms / 1000.0
    splits = [0.0]
    prev_end = 0.0
    for word in words:
        gap = word.start - prev_end
        if prev_end > 0 and gap >= pause:
            splits.append(word.start if gap < pause * 4 else prev_end)
        prev_end = word.end
    return scenes_from_splits(splits, duration, words, min_scene=min_scene)


def ffmpeg_silence_starts(
    wav: Path,
    *,
    pause_ms: int = DEFAULT_PAUSE_MS,
    noise_db: int = -30,
) -> list[float]:
    exe = shutil.which("ffmpeg")
    if not exe:
        return []
    noise = f"{noise_db}dB"
    duration = max(pause_ms / 1000.0, 0.08)
    result = subprocess.run(
        [
            exe,
            "-hide_banner",
            "-i",
            str(wav),
            "-af",
            f"silencedetect=noise={noise}:d={duration}",
            "-f",
            "null",
            "-",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    blob = (result.stderr or "") + (result.stdout or "")
    starts: list[float] = []
    for match in re.finditer(r"silence_start:\s*([0-9.]+)", blob):
        starts.append(float(match.group(1)))
    return starts


def whisper_words(wav: Path) -> list[Word]:
    try:
        from faster_whisper import WhisperModel
    except ImportError as exc:
        raise RuntimeError(
            "faster-whisper is not installed. Pause detection falls back to "
            "ffmpeg silencedetect, or install: pip install faster-whisper"
        ) from exc
    model = WhisperModel("base.en", device="cpu", compute_type="int8")
    segments, _info = model.transcribe(
        str(wav), word_timestamps=True, language="en", beam_size=1
    )
    words: list[Word] = []
    for segment in segments:
        for item in segment.words or []:
            text = str(getattr(item, "word", "") or "").strip()
            if not text:
                continue
            words.append(
                Word(
                    text=text,
                    start=float(getattr(item, "start", 0.0) or 0.0),
                    end=float(getattr(item, "end", 0.0) or 0.0),
                )
            )
    return words


def audio_duration_seconds(path: Path) -> float:
    if path.suffix.lower() == ".wav":
        with wave.open(str(path), "rb") as handle:
            frames = handle.getnframes()
            rate = handle.getframerate()
            if rate:
                return frames / float(rate)
    exe = shutil.which("ffprobe")
    if not exe:
        raise RuntimeError("ffprobe is required to measure imported audio")
    result = subprocess.run(
        [
            exe,
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=nw=1:nk=1",
            str(path),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    return float(result.stdout.strip())


def detect_pauses(
    wav: Path,
    *,
    pause_ms: int = DEFAULT_PAUSE_MS,
    min_scene: float = MIN_SCENE_SECONDS,
    words: list[Word] | None = None,
) -> dict[str, Any]:
    duration = audio_duration_seconds(wav)
    used_words = words
    if used_words is None:
        try:
            used_words = whisper_words(wav)
        except Exception:
            used_words = []
    splits = [0.0]
    if used_words:
        pause = pause_ms / 1000.0
        prev_end = 0.0
        for word in used_words:
            if prev_end > 0 and (word.start - prev_end) >= pause:
                splits.append(prev_end)
            prev_end = word.end
    for start in ffmpeg_silence_starts(wav, pause_ms=pause_ms):
        splits.append(start)
    scenes = scenes_from_splits(splits, duration, used_words or None, min_scene=min_scene)
    return timestamp_table(scenes, duration, pause_ms=pause_ms, audio=str(wav))


def timestamp_table(
    scenes: list[PauseScene],
    duration: float,
    *,
    pause_ms: int = DEFAULT_PAUSE_MS,
    audio: str = "",
) -> dict[str, Any]:
    rows = [
        {
            "index": scene.index,
            "start": scene.start,
            "end": scene.end,
            "start_tc": scene.timestamp,
            "filename": scene.filename,
            "text": scene.text,
        }
        for scene in scenes
    ]
    return {
        "audio": audio,
        "duration_seconds": round(float(duration), 3),
        "pause_min_ms": int(pause_ms),
        "scene_count": len(rows),
        "scenes": rows,
    }


def transcript_text(table: dict[str, Any]) -> str:
    lines = []
    for row in table.get("scenes") or []:
        tc = row.get("start_tc") or format_mmss(float(row.get("start") or 0))
        text = str(row.get("text") or "").strip()
        lines.append(f"[{tc}] {text}".rstrip())
    return "\n".join(lines) + ("\n" if lines else "")


def write_timestamps(table: dict[str, Any], dest: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(table, indent=2) + "\n", encoding="utf-8")
    return dest


def write_transcript(table: dict[str, Any], dest: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(transcript_text(table), encoding="utf-8")
    return dest


def load_timestamps(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_tone_silence_wav(
    dest: Path,
    *,
    sample_rate: int = 16000,
    tone_seconds: float = 1.0,
    silence_seconds: float = 0.5,
    repeats: int = 2,
) -> Path:
    """Synthetic wav for tests: tone, silence, tone… No ElevenLabs file needed."""
    import math

    dest.parent.mkdir(parents=True, exist_ok=True)
    chunks: list[bytes] = []
    for i in range(repeats):
        n_tone = int(tone_seconds * sample_rate)
        buf = bytearray()
        for n in range(n_tone):
            sample = int(16000 * math.sin(2 * math.pi * 440 * n / sample_rate))
            buf.extend(struct.pack("<h", sample))
        chunks.append(bytes(buf))
        if i < repeats - 1:
            n_sil = int(silence_seconds * sample_rate)
            chunks.append(b"\x00\x00" * n_sil)
    payload = b"".join(chunks)
    with wave.open(str(dest), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(sample_rate)
        handle.writeframes(payload)
    return dest
