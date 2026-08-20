"""
ElevenLabs TTS voice adapter — paid, higher-expressiveness narration with
exact per-shot timing.

Like ``adapters.voice.edge``, consecutive narrated shots are synthesised as
ONE continuous utterance per run (natural storytelling delivery, no
slideshow-of-captions cadence) and a deliberately empty beat gets a silent
segment of its own instead. Where this differs from edge-tts: ElevenLabs'
``convert_with_timestamps`` endpoint returns a start/end time for every
CHARACTER of the exact text sent, not just word-boundary events for its own
internal tokenisation — so there is no tokeniser-mismatch reconciliation to
do (contrast ``edge.py``'s ``_align_word_offsets``): a word's start offset is
just the alignment timestamp of that word's first character in the original
string.

Default voice is configurable via the ``ELEVENLABS_VOICE_ID`` environment
variable (fallback: Liam — "TX3LPaxmHKxFdv7VOQHJ", ElevenLabs' own
"energetic, social media creator" premade voice — a closer match to this
format's punchy, propulsive delivery than a slower "warm storyteller" voice,
verified 2026-08-16 by generating and comparing short samples of both against
real script beats). Community/shared "voice library" voices (as opposed to
ElevenLabs' own premade voices) require a paid plan to use via the API even
when a pay-as-you-go card is on file — verified empirically, not documented
up front by the error message it raises.
"""

from __future__ import annotations

import asyncio
import base64
import hashlib
import os
import re
import tempfile
from pathlib import Path

from elevenlabs.client import AsyncElevenLabs

from adapters import _cache, pricing
from adapters.voice import _audio
from adapters.voice.base import VoiceAdapter, VoiceoverResult
from adapters.voice.edge import split_run_durations
from graph.assets import save_asset

# Liam — Energetic, Social Media Creator (verified 2026-08-16).
# Override via ELEVENLABS_VOICE_ID in .env.
_FALLBACK_VOICE_ID = "TX3LPaxmHKxFdv7VOQHJ"
_DEFAULT_MODEL = "eleven_multilingual_v2"
_OUTPUT_FORMAT = "mp3_44100_128"
_SAMPLE_RATE = 44100

# A touch more expressive/energetic than the API default (0.0-1.0 scale):
# higher style pushes delivery toward the voice's expressive extremes
# (better "up-vibe" narration for an explainer/storytelling format), and
# slightly lower stability keeps prosody from going flat over a long
# continuous run. speaker_boost trades a little latency for clearer timbre.
_VOICE_SETTINGS = {
    "stability": 0.4,
    "similarity_boost": 0.8,
    "style": 0.35,
    "use_speaker_boost": True,
}


def _word_spans(text: str) -> list[tuple[int, int]]:
    """(start, end) character index of every whitespace-delimited word."""
    return [(m.start(), m.end()) for m in re.finditer(r"\S+", text)]


class ElevenLabsVoiceAdapter(VoiceAdapter):
    """
    ElevenLabs wrapper for narration synthesis with exact per-shot timing.

    ``ELEVENLABS_API_KEY`` must be set in the environment.
    ``ELEVENLABS_VOICE_ID`` is optional; falls back to George.
    """

    def __init__(self) -> None:
        api_key = os.environ.get("ELEVENLABS_API_KEY")
        self._client = AsyncElevenLabs(api_key=api_key)
        self._default_voice_id = os.environ.get(
            "ELEVENLABS_VOICE_ID", _FALLBACK_VOICE_ID
        )

    async def _synthesize_with_char_alignment(
        self, text: str, voice_id: str
    ) -> tuple[bytes, list[str], list[float], list[float]]:
        response = await self._client.text_to_speech.convert_with_timestamps(
            voice_id=voice_id,
            text=text,
            model_id=_DEFAULT_MODEL,
            output_format=_OUTPUT_FORMAT,
            voice_settings=_VOICE_SETTINGS,
        )
        audio_bytes = base64.b64decode(response.audio_base_64)
        alignment = response.alignment
        if alignment is None:
            return audio_bytes, [], [], []
        return (
            audio_bytes,
            list(alignment.characters),
            list(alignment.character_start_times_seconds),
            list(alignment.character_end_times_seconds),
        )

    async def synthesize(
        self,
        script_beats: list[str],
        shot_durations: list[float],
        voice_id: str = "default",
    ) -> VoiceoverResult:
        """
        Synthesise one audio track for the whole script.

        ``script_beats`` is shot-aligned: entry *i* is the narration for shot
        *i*. Consecutive non-empty entries are spoken as one continuous
        utterance; an empty entry is a deliberate gap and gets
        ``shot_durations[i]`` of real silence instead.
        """
        if not script_beats:
            script_beats = ["Perspective shift."]
        resolved_voice_id = (
            self._default_voice_id if voice_id == "default" else voice_id
        )

        cache_key = _cache.make_key(
            {
                "provider": "elevenlabs",
                "model": _DEFAULT_MODEL,
                "voice_id": resolved_voice_id,
                "output_format": _OUTPUT_FORMAT,
                "voice_settings": _VOICE_SETTINGS,
                "beats": list(script_beats),
                "silences": [
                    shot_durations[i] if i < len(shot_durations) else 0.0
                    for i, b in enumerate(script_beats)
                    if not (b or "").strip()
                ],
            }
        )
        cached = _cache.load("elevenlabs_voiceover", cache_key)
        if cached is not None:
            # A cache hit makes no new API call, so this run spends $0 here.
            return VoiceoverResult(
                audio_url=cached["audio_url"],
                duration_seconds=cached["duration_seconds"],
                beat_durations=cached["beat_durations"],
                cost_usd=0.0,
            )

        # Group into alternating (speech run) / (single silent gap) segments,
        # preserving beat order so concatenation reproduces the script.
        segments: list[tuple[str, list[int]]] = []  # ("speech"|"silence", beat indices)
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
        total_chars = 0

        try:
            with tempfile.TemporaryDirectory(prefix="pe_el_") as tmp:
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
                        text = " ".join(script_beats[i].strip() for i in indices)
                        total_chars += len(text)
                        (
                            audio_bytes,
                            chars,
                            starts,
                            ends,
                        ) = await self._synthesize_with_char_alignment(
                            text, resolved_voice_id
                        )
                        part.write_bytes(audio_bytes)
                        run_total = await asyncio.to_thread(
                            _audio.duration_seconds, part
                        )
                        beat_words = [script_beats[i].strip().split() for i in indices]
                        word_counts = [len(w) for w in beat_words]
                        word_offsets: list[float] | None = None
                        if len(chars) == len(text) and starts:
                            spans = _word_spans(text)
                            if len(spans) == sum(word_counts):
                                word_offsets = [starts[start] for start, _ in spans]
                        durations = split_run_durations(
                            word_counts, word_offsets, run_total
                        )
                        for i, d in zip(indices, durations, strict=True):
                            beat_durations[i] = d
                    parts.append(part)

                out = tmp_path / "full.mp3"
                await asyncio.to_thread(_audio.concat_mp3, parts, out, _SAMPLE_RATE)
                audio_bytes = out.read_bytes()
                total = await asyncio.to_thread(_audio.duration_seconds, out)
        except Exception as exc:
            raise RuntimeError(f"ElevenLabs TTS failed: {exc}") from exc

        digest = hashlib.sha1("\n".join(script_beats).encode("utf-8")).hexdigest()[:16]
        audio_url = save_asset(f"audio/voiceover_elevenlabs_{digest}.mp3", audio_bytes)
        _cache.store(
            "elevenlabs_voiceover",
            cache_key,
            {
                "audio_url": audio_url,
                "duration_seconds": total,
                "beat_durations": beat_durations,
            },
        )
        cost_usd = pricing.elevenlabs_tts_cost(total_chars)
        return VoiceoverResult(
            audio_url=audio_url,
            duration_seconds=total,
            beat_durations=beat_durations,
            cost_usd=cost_usd,
        )
