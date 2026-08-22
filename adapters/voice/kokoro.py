"""
Free local Kokoro-82M TTS (ONNX, Apache 2.0) — Liam-class punch without a paid API.

Consecutive narrated shots are synthesised in ~80-word packs so phoneme
timings stay aligned. Empty beats get real silence. Phoneme-word starts are
fit onto ``str.split()`` (interpolated if the counts differ by a few);
durations still sum to the pack length, so picture cannot drift from audio.

Requires ``pip install kokoro-onnx soundfile espeakng-loader`` and the two
model files under ``assets/models/kokoro/`` (gitignored with the rest of
``assets/``). Override voice with ``KOKORO_VOICE`` (default ``am_liam``,
speed 1.0, ~205 wpm long-form — set ``NARRATION_WPM=205`` when chunking).
"""

from __future__ import annotations

import asyncio
import hashlib
import os
import tempfile
from pathlib import Path

from adapters import _cache
from adapters.voice import _audio
from adapters.voice.base import VoiceAdapter, VoiceoverResult
from adapters.voice.edge import split_run_durations
from graph.assets import save_asset

_REPO_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_MODEL_DIR = _REPO_ROOT / "assets" / "models" / "kokoro"
_DEFAULT_VOICE = "am_liam"
_SPEED = 1.0
_LANG = "en-us"
_SAMPLE_RATE = 24000
# Long-form packs keep phoneme-word alignment stable. One giant utterance
# drifted (~210–250 wpm, offset counts off by a few words) and the picture
# cut in the middle of the breath.
_PACK_WORDS = 80

_engine = None


def _model_dir() -> Path:
    override = os.environ.get("KOKORO_MODEL_DIR")
    return Path(override) if override else _DEFAULT_MODEL_DIR


def _engine_singleton():
    global _engine
    if _engine is not None:
        return _engine
    try:
        from kokoro_onnx import Kokoro
    except ImportError as exc:
        raise RuntimeError(
            "Kokoro TTS is not installed. Run: "
            "pip install kokoro-onnx soundfile espeakng-loader"
        ) from exc
    model_dir = _model_dir()
    model = model_dir / "kokoro-v1.0.onnx"
    voices = model_dir / "voices-v1.0.bin"
    if not model.is_file() or not voices.is_file():
        raise RuntimeError(
            f"Kokoro model files missing in {model_dir}. Need kokoro-v1.0.onnx "
            "and voices-v1.0.bin from "
            "https://github.com/thewh1teagle/kokoro-onnx/releases"
        )
    _engine = Kokoro(str(model), str(voices))
    return _engine


def _wav_to_mp3(wav: Path, mp3: Path) -> None:
    import subprocess

    subprocess.run(
        [
            _audio.ffmpeg(),
            "-y",
            "-i",
            str(wav),
            "-c:a",
            "libmp3lame",
            "-b:a",
            _audio.BITRATE,
            "-ar",
            str(_SAMPLE_RATE),
            "-ac",
            "1",
            str(mp3),
        ],
        check=True,
        capture_output=True,
    )


def _resize_offsets(
    offsets: list[float], n_words: int, run_total: float
) -> list[float] | None:
    """Fit phoneme-word starts onto the naive word count.

    Kokoro sometimes emits a few more or fewer space-delimited phoneme
    words than ``str.split()`` (hyphens, years, initials). Interpolating
    keeps pause structure instead of throwing the whole run onto a flat
    word-count proportion, which is what made cuts land mid-breath.
    """
    if n_words <= 0:
        return None
    if len(offsets) == n_words:
        return offsets
    if len(offsets) < 2:
        return None
    import numpy as np

    src_x = np.linspace(0.0, 1.0, len(offsets))
    dst_x = np.linspace(0.0, 1.0, n_words)
    fitted = np.interp(dst_x, src_x, np.asarray(offsets, dtype=float))
    return [float(max(0.0, min(run_total, x))) for x in fitted]


def _pack_indices(indices: list[int], script_beats: list[str]) -> list[list[int]]:
    """Split a speech run into ~_PACK_WORDS windows, breaking on chunk ends."""
    packs: list[list[int]] = []
    current: list[int] = []
    words = 0
    for i in indices:
        n = len(script_beats[i].strip().split())
        if current and words + n > _PACK_WORDS:
            packs.append(current)
            current = []
            words = 0
        current.append(i)
        words += n
    if current:
        packs.append(current)
    return packs


def _word_offsets_from_timings(spoken) -> list[float] | None:
    """Start time of each whitespace-delimited phoneme-word, if timings exist."""
    if not spoken:
        return None
    offsets: list[float] = []
    in_word = False
    for event in spoken:
        if (event.phoneme or "").strip() == "":
            in_word = False
            continue
        if not in_word:
            offsets.append(float(event.start))
            in_word = True
    return offsets or None


def _synthesize_text(text: str, voice: str) -> tuple[bytes, list[float] | None]:
    import soundfile as sf

    engine = _engine_singleton()
    audio, rate, spoken = engine.create_timed(
        text,
        voice=voice,
        speed=_SPEED,
        lang=_LANG,
        trim=True,
        sentence_pause=0.22,
        clause_pause=0.10,
    )
    offsets = _word_offsets_from_timings(spoken)
    with tempfile.TemporaryDirectory(prefix="pe_kokoro_") as tmp:
        wav = Path(tmp) / "utt.wav"
        mp3 = Path(tmp) / "utt.mp3"
        sf.write(wav, audio, rate)
        _wav_to_mp3(wav, mp3)
        return mp3.read_bytes(), offsets


class KokoroVoiceAdapter(VoiceAdapter):
    """Local Kokoro-82M narration. Cost is always $0."""

    def __init__(self, voice: str | None = None) -> None:
        self._voice = voice or os.environ.get("KOKORO_VOICE", _DEFAULT_VOICE)

    async def synthesize(
        self,
        script_beats: list[str],
        shot_durations: list[float],
        voice_id: str = "default",
    ) -> VoiceoverResult:
        if not script_beats:
            script_beats = ["Perspective shift."]
        resolved_voice = self._voice if voice_id == "default" else voice_id

        cache_key = _cache.make_key(
            {
                "provider": "kokoro-onnx",
                "voice": resolved_voice,
                "speed": _SPEED,
                "pack_words": _PACK_WORDS,
                "lang": _LANG,
                "beats": list(script_beats),
                "silences": [
                    shot_durations[i] if i < len(shot_durations) else 0.0
                    for i, b in enumerate(script_beats)
                    if not (b or "").strip()
                ],
            }
        )
        cached = _cache.load("kokoro_voiceover", cache_key)
        if cached is not None:
            return VoiceoverResult(
                audio_url=cached["audio_url"],
                duration_seconds=cached["duration_seconds"],
                beat_durations=cached["beat_durations"],
                cost_usd=0.0,
            )

        segments: list[tuple[str, list[int]]] = []
        run: list[int] = []
        for i, raw in enumerate(script_beats):
            if (raw or "").strip():
                run.append(i)
            else:
                if run:
                    segments.append(("speech", run))
                    run = []
                segments.append(("silence", [i]))
        if run:
            segments.append(("speech", run))

        beat_durations: list[float] = [0.0] * len(script_beats)

        with tempfile.TemporaryDirectory(prefix="pe_kokoro_") as tmp:
            tmp_path = Path(tmp)
            parts: list[Path] = []

            for seg_idx, (kind, indices) in enumerate(segments):
                part = tmp_path / f"seg_{seg_idx:03d}.mp3"
                if kind == "silence":
                    i = indices[0]
                    gap = shot_durations[i] if i < len(shot_durations) else 1.0
                    await asyncio.to_thread(
                        _audio.silence_mp3, part, gap, _SAMPLE_RATE
                    )
                    beat_durations[i] = round(gap, 3)
                else:
                    packs = _pack_indices(indices, script_beats)
                    pack_files: list[Path] = []
                    for pack_i, pack in enumerate(packs):
                        pack_path = tmp_path / f"seg_{seg_idx:03d}_{pack_i:02d}.mp3"
                        text = " ".join(script_beats[i].strip() for i in pack)
                        audio_bytes, phoneme_offsets = await asyncio.to_thread(
                            _synthesize_text, text, resolved_voice
                        )
                        pack_path.write_bytes(audio_bytes)
                        run_total = await asyncio.to_thread(
                            _audio.duration_seconds, pack_path
                        )
                        beat_words = [script_beats[i].strip().split() for i in pack]
                        word_counts = [len(w) for w in beat_words]
                        naive_n = sum(word_counts)
                        word_offsets = (
                            _resize_offsets(phoneme_offsets, naive_n, run_total)
                            if phoneme_offsets
                            else None
                        )
                        durations = split_run_durations(
                            word_counts, word_offsets, run_total
                        )
                        for i, d in zip(pack, durations, strict=True):
                            beat_durations[i] = d
                        pack_files.append(pack_path)
                    if len(pack_files) == 1:
                        pack_files[0].replace(part)
                    else:
                        await asyncio.to_thread(
                            _audio.concat_mp3, pack_files, part, _SAMPLE_RATE
                        )
                parts.append(part)

            out = tmp_path / "full.mp3"
            await asyncio.to_thread(_audio.concat_mp3, parts, out, _SAMPLE_RATE)
            audio_bytes = out.read_bytes()
            total = await asyncio.to_thread(_audio.duration_seconds, out)

        digest = hashlib.sha1("\n".join(script_beats).encode("utf-8")).hexdigest()[:16]
        audio_url = save_asset(f"audio/voiceover_kokoro_{digest}.mp3", audio_bytes)
        _cache.store(
            "kokoro_voiceover",
            cache_key,
            {
                "audio_url": audio_url,
                "duration_seconds": total,
                "beat_durations": beat_durations,
            },
        )
        return VoiceoverResult(
            audio_url=audio_url,
            duration_seconds=total,
            beat_durations=beat_durations,
            cost_usd=0.0,
        )
