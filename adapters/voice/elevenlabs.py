"""
ElevenLabs TTS voice adapter.

Joins all script beats into a single narration string, synthesises it via
the ElevenLabs API, saves the resulting MP3 to the local asset store, and
returns the file:// URL plus an estimated duration.

Default voice is configurable via the ``ELEVENLABS_VOICE_ID`` environment
variable (fallback: Rachel — "21m00Tcm4TlvDq8ikWAM").
"""

from __future__ import annotations

import os

from elevenlabs.client import AsyncElevenLabs

from adapters import _cache
from adapters.voice.base import VoiceAdapter, VoiceoverResult
from graph.assets import save_asset

# Rachel's voice ID — a well-known ElevenLabs default voice.
_FALLBACK_VOICE_ID = "21m00Tcm4TlvDq8ikWAM"
_DEFAULT_MODEL = "eleven_multilingual_v2"
_OUTPUT_FORMAT = "mp3_44100_128"


class ElevenLabsVoiceAdapter(VoiceAdapter):
    """
    Thin ElevenLabs wrapper for narration synthesis.

    ``ELEVENLABS_API_KEY`` must be set in the environment.
    ``ELEVENLABS_VOICE_ID`` is optional; falls back to Rachel.
    """

    def __init__(self) -> None:
        api_key = os.environ.get("ELEVENLABS_API_KEY")
        self._client = AsyncElevenLabs(api_key=api_key)
        self._default_voice_id = os.environ.get(
            "ELEVENLABS_VOICE_ID", _FALLBACK_VOICE_ID
        )

    async def synthesize(
        self,
        script_beats: list[str],
        shot_durations: list[float],
        voice_id: str = "default",
    ) -> VoiceoverResult:
        """
        Join beats into narration, call ElevenLabs TTS, and save the MP3.

        Duration is estimated as the sum of shot durations (a close proxy
        for the actual audio length in a tightly-edited video).
        """
        narration = " ".join(beat.strip() for beat in script_beats if beat.strip())
        if not narration:
            narration = "Perspective shift."

        resolved_voice_id = (
            self._default_voice_id if voice_id == "default" else voice_id
        )
        total_duration = sum(shot_durations) if shot_durations else 30.0

        cache_key = _cache.make_key(
            {
                "model": _DEFAULT_MODEL,
                "voice_id": resolved_voice_id,
                "output_format": _OUTPUT_FORMAT,
                "narration": narration,
            }
        )
        cached = _cache.load("elevenlabs_voiceover", cache_key)
        if cached is not None:
            return VoiceoverResult(
                audio_url=cached["audio_url"],
                duration_seconds=cached.get("duration_seconds", total_duration),
            )

        try:
            # convert() on AsyncElevenLabs is an async generator — do not await it,
            # iterate it directly to collect byte chunks.
            chunks: list[bytes] = []
            async for chunk in self._client.text_to_speech.convert(
                text=narration,
                voice_id=resolved_voice_id,
                model_id=_DEFAULT_MODEL,
                output_format=_OUTPUT_FORMAT,
            ):
                if isinstance(chunk, bytes) and chunk:
                    chunks.append(chunk)
            audio_bytes = b"".join(chunks)

        except Exception as exc:
            raise RuntimeError(f"ElevenLabs TTS failed: {exc}") from exc

        # Content-addressed filename so a cached entry maps to a file that
        # still exists on disk across re-runs.
        audio_url = save_asset(f"audio/voiceover_{cache_key[:16]}.mp3", audio_bytes)
        _cache.store(
            "elevenlabs_voiceover",
            cache_key,
            {"audio_url": audio_url, "duration_seconds": total_duration},
        )
        return VoiceoverResult(audio_url=audio_url, duration_seconds=total_duration)
