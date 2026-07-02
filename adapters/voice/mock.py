"""
Deterministic mock TTS adapter for Phase 1 (local skeleton).
"""

from __future__ import annotations

from adapters.voice.base import VoiceAdapter, VoiceoverResult
from graph.assets import local_asset_url


class MockVoiceAdapter(VoiceAdapter):
    """Stand-in TTS adapter that returns a placeholder audio URL."""

    async def synthesize(
        self,
        script_beats: list[str],
        shot_durations: list[float],
        voice_id: str = "default",
    ) -> VoiceoverResult:
        total_duration = sum(shot_durations) if shot_durations else 30.0
        url = local_asset_url("audio/voiceover.mp3")
        return VoiceoverResult(audio_url=url, duration_seconds=total_duration)
