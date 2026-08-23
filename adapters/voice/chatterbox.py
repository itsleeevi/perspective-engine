"""
Chatterbox-Turbo narration (MIT, Resemble AI) — the free voice that stops
sounding like TTS.

Kokoro reads cleanly but flat; Chatterbox is an 0.5B/350M Llama-backbone TTS
with an emotion dial that wins blind tests against paid APIs. It is
GPU-oriented, but for offline video rendering ~1x real-time on 8 CPU cores
is perfectly acceptable — a 6-minute VO costs a coffee break, not money.

Torch and the model live in an isolated ``.venv-tts`` (see
``scripts/tts_worker.py``); this adapter shells out to that interpreter so
the main pipeline venv never depends on torch. All packs go in ONE worker
call, so the model loads once.

Timing: Chatterbox reports no word offsets, so the worker force-aligns its
own output with faster-whisper (word timestamps) and this adapter reconciles
those tokens against ``str.split()`` via the same ``_align_word_offsets``
used for edge-tts. Cuts therefore land on measured speech, no matter which
engine produced it — that is the systemic sync fix.

Naturalness, beyond the engine itself:

- A **breath** (~0.3s of real silence) is inserted between packs inside a
  speech run, credited to the beat that ends the earlier pack. Humans breathe
  between thoughts; back-to-back packs with no gap is the one place the seam
  between generations is audible. Cuts also land inside these silences.
- Narration may contain Chatterbox paralinguistic tags (``[sigh]``,
  ``[chuckle]``, ...). They are spoken as sounds but stripped before word
  counting so forced alignment still reconciles.
- The finished track is loudness-normalised to -16 LUFS (YouTube VO level),
  so pack-to-pack level drift from separate generations is ironed out.

Env:
    CHATTERBOX_MODEL      "turbo" (default) or "nano" (fastest, 110M)
    CHATTERBOX_VOICE_REF  path to a 5-10s wav to clone the narrator from
    CHATTERBOX_EXAGGERATION  emotion dial, default 0.5 (0=flat, 1=theatrical)
    CHATTERBOX_TEMPERATURE   sampler heat, default 0.9 (0.7 flat, 1.0+ wanders)
    CHATTERBOX_BREATH        inter-pack pause seconds, default 0.30
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import re
import subprocess
import tempfile
from pathlib import Path

from adapters import _cache
from adapters.voice import _audio
from adapters.voice.base import VoiceAdapter, VoiceoverResult
from adapters.voice.edge import _align_word_offsets, split_run_durations
from adapters.voice.years import speak_years
from graph.assets import save_asset

_REPO_ROOT = Path(__file__).resolve().parents[2]
_WORKER = _REPO_ROOT / "scripts" / "tts_worker.py"
_TTS_PYTHON = _REPO_ROOT / ".venv-tts" / "bin" / "python"

# ~60 words ≈ 20s of speech: inside Chatterbox's comfortable generation
# window, long enough that prosody flows like telling a story instead of
# reading captions. Packs break only on chunk boundaries so alignment maps
# cleanly back onto shots.
_PACK_WORDS = 60

# Chatterbox speaks these as non-verbal sounds; strip them before counting
# words so whisper alignment still lines up one-to-one.
_PARALINGUISTIC = re.compile(
    r"\[(?:laugh|chuckle|sigh|cough|sniff|gasp|groan|clear throat)\]", re.I
)


def _spoken_words(text: str) -> list[str]:
    return _PARALINGUISTIC.sub(" ", text).split()


def _worker_available() -> bool:
    return _TTS_PYTHON.is_file()


def _pack_indices(indices: list[int], script_beats: list[str]) -> list[list[int]]:
    packs: list[list[int]] = []
    current: list[int] = []
    words = 0
    for i in indices:
        n = len(_spoken_words(script_beats[i]))
        if current and words + n > _PACK_WORDS:
            packs.append(current)
            current = []
            words = 0
        current.append(i)
        words += n
    if current:
        packs.append(current)
    return packs


def _run_worker(job: dict) -> dict:
    if not _worker_available():
        raise RuntimeError(
            "Chatterbox venv missing. Create it with:\n"
            "  python3 -m venv .venv-tts && .venv-tts/bin/pip install "
            "chatterbox-tts faster-whisper soundfile "
            "--extra-index-url https://download.pytorch.org/whl/cpu"
        )
    proc = subprocess.run(
        [str(_TTS_PYTHON), str(_WORKER)],
        input=json.dumps(job),
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"tts_worker failed: {proc.stderr[-2000:]}")
    return json.loads(proc.stdout.strip().splitlines()[-1])


class ChatterboxVoiceAdapter(VoiceAdapter):
    """Local Chatterbox-Turbo narration with whisper-aligned timings. $0."""

    def __init__(self, voice_ref: str | None = None) -> None:
        self._voice_ref = voice_ref or os.environ.get("CHATTERBOX_VOICE_REF", "")
        self._model = os.environ.get("CHATTERBOX_MODEL", "turbo")
        self._exaggeration = float(os.environ.get("CHATTERBOX_EXAGGERATION", "0.5"))
        self._temperature = float(os.environ.get("CHATTERBOX_TEMPERATURE", "0.9"))
        self._breath = float(os.environ.get("CHATTERBOX_BREATH", "0.30"))

    async def synthesize(
        self,
        script_beats: list[str],
        shot_durations: list[float],
        voice_id: str = "default",
    ) -> VoiceoverResult:
        if not script_beats:
            script_beats = ["Perspective shift."]

        cache_key = _cache.make_key(
            {
                "provider": "chatterbox",
                "model": self._model,
                "voice_ref": self._voice_ref,
                "exaggeration": self._exaggeration,
                "temperature": self._temperature,
                "breath": self._breath,
                "loudnorm": True,
                "pack_words": _PACK_WORDS,
                "year_speak": 1,
                "beats": list(script_beats),
                "silences": [
                    shot_durations[i] if i < len(shot_durations) else 0.0
                    for i, b in enumerate(script_beats)
                    if not (b or "").strip()
                ],
            }
        )
        cached = _cache.load("chatterbox_voiceover", cache_key)
        if cached is not None:
            return VoiceoverResult(
                audio_url=cached["audio_url"],
                duration_seconds=cached["duration_seconds"],
                beat_durations=cached["beat_durations"],
                cost_usd=0.0,
            )

        # Alternating speech runs / silent gaps, same contract as edge/kokoro.
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

        spoken_beats = [
            speak_years(raw.strip()) if (raw or "").strip() else (raw or "")
            for raw in script_beats
        ]

        # Collect every pack across all speech runs into one worker call.
        pack_specs: list[tuple[int, list[int]]] = []  # (segment idx, beat indices)
        for seg_idx, (kind, indices) in enumerate(segments):
            if kind != "speech":
                continue
            for pack in _pack_indices(indices, spoken_beats):
                pack_specs.append((seg_idx, pack))

        beat_durations: list[float] = [0.0] * len(script_beats)

        with tempfile.TemporaryDirectory(prefix="pe_chatterbox_") as tmp:
            tmp_path = Path(tmp)

            job = {
                "packs": [
                    " ".join(spoken_beats[i].strip() for i in pack)
                    for _seg, pack in pack_specs
                ],
                "out_dir": str(tmp_path / "packs"),
                "voice_ref": self._voice_ref or None,
                "exaggeration": self._exaggeration,
                "temperature": self._temperature,
                "cfg_weight": 0.5,
                "model": self._model,
            }
            result = await asyncio.to_thread(_run_worker, job)
            pack_results = result["packs"]

            # Distribute measured pack time onto its beats via aligned words.
            seg_pack_files: dict[int, list[tuple[Path, int]]] = {}
            for (seg_idx, pack), pres in zip(pack_specs, pack_results, strict=True):
                wav = Path(pres["wav"])
                mp3 = wav.with_suffix(".mp3")
                await asyncio.to_thread(_wav_to_mp3, wav, mp3)
                run_total = await asyncio.to_thread(_audio.duration_seconds, mp3)

                beat_words = [_spoken_words(spoken_beats[i]) for i in pack]
                word_counts = [len(w) for w in beat_words]
                naive_words = [w for beat in beat_words for w in beat]
                events = [(w, t, 0.0) for w, t in pres["words"]]
                word_offsets = _align_word_offsets(naive_words, events)
                durations = split_run_durations(word_counts, word_offsets, run_total)
                for i, d in zip(pack, durations, strict=True):
                    beat_durations[i] = d
                seg_pack_files.setdefault(seg_idx, []).append((mp3, pack[-1]))

            # A breath of real silence between packs inside a run; its time is
            # credited to the beat that ends the earlier pack so per-shot
            # durations still sum exactly to the track.
            parts: list[Path] = []
            breath_n = 0
            for seg_idx, (kind, indices) in enumerate(segments):
                if kind == "silence":
                    i = indices[0]
                    gap = shot_durations[i] if i < len(shot_durations) else 1.0
                    part = tmp_path / f"sil_{seg_idx:03d}.mp3"
                    await asyncio.to_thread(_audio.silence_mp3, part, gap)
                    beat_durations[i] = round(gap, 3)
                    parts.append(part)
                    continue
                pack_files = seg_pack_files[seg_idx]
                for j, (mp3, last_beat) in enumerate(pack_files):
                    parts.append(mp3)
                    if self._breath > 0 and j < len(pack_files) - 1:
                        breath = tmp_path / f"breath_{breath_n:03d}.mp3"
                        breath_n += 1
                        await asyncio.to_thread(
                            _audio.silence_mp3, breath, self._breath
                        )
                        real = await asyncio.to_thread(
                            _audio.duration_seconds, breath
                        )
                        beat_durations[last_beat] = round(
                            beat_durations[last_beat] + real, 3
                        )
                        parts.append(breath)

            raw = tmp_path / "raw.mp3"
            await asyncio.to_thread(_audio.concat_mp3, parts, raw)
            out = tmp_path / "full.mp3"
            await asyncio.to_thread(_loudnorm, raw, out)
            audio_bytes = out.read_bytes()
            total = await asyncio.to_thread(_audio.duration_seconds, out)

        digest = hashlib.sha1("\n".join(script_beats).encode("utf-8")).hexdigest()[:16]
        audio_url = save_asset(f"audio/voiceover_chatterbox_{digest}.mp3", audio_bytes)
        _cache.store(
            "chatterbox_voiceover",
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


def _loudnorm(src: Path, dest: Path) -> None:
    """
    Normalise the whole track to -16 LUFS (YouTube voice-over level).

    Packs are separate generations and drift a little in level; one pass over
    the finished track evens them out. ffmpeg's loudnorm preserves duration,
    so the measured per-beat durations stay valid.
    """
    subprocess.run(
        [
            _audio.ffmpeg(), "-y", "-i", str(src),
            "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
            "-c:a", "libmp3lame", "-b:a", _audio.BITRATE,
            "-ar", "44100", "-ac", "1",
            str(dest),
        ],
        check=True,
        capture_output=True,
    )


def _wav_to_mp3(wav: Path, mp3: Path) -> None:
    subprocess.run(
        [
            _audio.ffmpeg(), "-y", "-i", str(wav),
            "-c:a", "libmp3lame", "-b:a", _audio.BITRATE, "-ac", "1",
            str(mp3),
        ],
        check=True,
        capture_output=True,
    )
