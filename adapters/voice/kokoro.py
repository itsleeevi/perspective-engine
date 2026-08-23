"""
Free local Kokoro-82M TTS (ONNX, Apache 2.0) — Liam-class punch without a paid API.

Consecutive narrated shots are synthesised one scene at a time. A short
hold of silence is appended to each scene so the picture cut lands on a
breath instead of mid-flow — packing several shots into one utterance made
the read robotic and the cuts drift. Empty beats (chapter cards) stay real
silence.

Requires ``pip install kokoro-onnx soundfile espeakng-loader`` and the two
model files under ``assets/models/kokoro/`` (gitignored with the rest of
``assets/``). Override voice with ``KOKORO_VOICE`` (default ``am_liam``,
speed 0.80). Channel cuts use ``am_liam`` at ~1.15 with a short hold
between scenes so the picture can change on a breath.
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
from adapters.voice.years import speak_years
from graph.assets import save_asset

_REPO_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_MODEL_DIR = _REPO_ROOT / "assets" / "models" / "kokoro"
_DEFAULT_VOICE = "am_liam"
_SPEED = float(os.environ.get("KOKORO_SPEED", "0.80"))
_LANG = "en-us"
_SAMPLE_RATE = 24000
_SENTENCE_PAUSE = float(os.environ.get("KOKORO_SENTENCE_PAUSE", "0.42"))
_CLAUSE_PAUSE = float(os.environ.get("KOKORO_CLAUSE_PAUSE", "0.18"))
# Hold this still after the line lands, then cut. 0 = no extra breath.
_SCENE_PAUSE = float(os.environ.get("KOKORO_SCENE_PAUSE", "0.0"))

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
        sentence_pause=_SENTENCE_PAUSE,
        clause_pause=_CLAUSE_PAUSE,
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
                "pack_words": 1,
                "sentence_pause": _SENTENCE_PAUSE,
                "clause_pause": _CLAUSE_PAUSE,
                "scene_pause": _SCENE_PAUSE,
                "lang": _LANG,
                "year_speak": 1,
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
        last_index = len(script_beats) - 1

        with tempfile.TemporaryDirectory(prefix="pe_kokoro_") as tmp:
            tmp_path = Path(tmp)
            atomic: list[Path] = []
            file_i = 0

            for kind, indices in segments:
                if kind == "silence":
                    i = indices[0]
                    gap = shot_durations[i] if i < len(shot_durations) else 1.0
                    part = tmp_path / f"atom_{file_i:04d}.mp3"
                    file_i += 1
                    await asyncio.to_thread(
                        _audio.silence_mp3, part, gap, _SAMPLE_RATE
                    )
                    atomic.append(part)
                    beat_durations[i] = round(
                        await asyncio.to_thread(_audio.duration_seconds, part), 3
                    )
                    continue
                for i in indices:
                    speech_path = tmp_path / f"atom_{file_i:04d}.mp3"
                    file_i += 1
                    text = speak_years(script_beats[i].strip())
                    audio_bytes, _offsets = await asyncio.to_thread(
                        _synthesize_text, text, resolved_voice
                    )
                    speech_path.write_bytes(audio_bytes)
                    atomic.append(speech_path)
                    speech_dur = await asyncio.to_thread(
                        _audio.duration_seconds, speech_path
                    )
                    pause = _SCENE_PAUSE if i < last_index and _SCENE_PAUSE > 0 else 0.0
                    if pause:
                        gap_path = tmp_path / f"atom_{file_i:04d}.mp3"
                        file_i += 1
                        await asyncio.to_thread(
                            _audio.silence_mp3, gap_path, pause, _SAMPLE_RATE
                        )
                        atomic.append(gap_path)
                        gap_dur = await asyncio.to_thread(
                            _audio.duration_seconds, gap_path
                        )
                        beat_durations[i] = round(speech_dur + gap_dur, 3)
                    else:
                        beat_durations[i] = round(speech_dur, 3)

            out = tmp_path / "full.mp3"
            await asyncio.to_thread(_audio.concat_mp3, atomic, out, _SAMPLE_RATE)
            audio_bytes = out.read_bytes()
            total = await asyncio.to_thread(_audio.duration_seconds, out)
            piece_sum = sum(beat_durations)
            if piece_sum > 0 and abs(total - piece_sum) > 0.02:
                scale = total / piece_sum
                beat_durations = [round(d * scale, 3) for d in beat_durations]
                beat_durations[-1] = round(
                    beat_durations[-1] + (total - sum(beat_durations)), 3
                )

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
