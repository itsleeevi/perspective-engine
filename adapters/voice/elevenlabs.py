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

        try:
            audio_response = await self._client.text_to_speech.convert(
                text=narration,
                voice_id=resolved_voice_id,
                model_id=_DEFAULT_MODEL,
                output_format=_OUTPUT_FORMAT,
            )

            # The async client returns an async iterator of byte chunks.
            chunks: list[bytes] = []
            async for chunk in audio_response:
                if isinstance(chunk, bytes) and chunk:
                    chunks.append(chunk)
            audio_bytes = b"".join(chunks)

        except Exception as exc:
            raise RuntimeError(f"ElevenLabs TTS failed: {exc}") from exc

        audio_url = save_asset("audio/voiceover.mp3", audio_bytes)
        total_duration = sum(shot_durations) if shot_durations else 30.0
        return VoiceoverResult(audio_url=audio_url, duration_seconds=total_duration)
