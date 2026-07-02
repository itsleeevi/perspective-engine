"""
Base interface for voice / TTS adapters.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class VoiceoverResult:
    """Output of a TTS call."""

    audio_url: str
    """URL of the generated audio file."""
    duration_seconds: float
    """Actual rendered duration."""


class VoiceAdapter(ABC):
    """Abstract TTS adapter."""

    @abstractmethod
    async def synthesize(
        self,
        script_beats: list[str],
        shot_durations: list[float],
        voice_id: str = "default",
    ) -> VoiceoverResult:
        """
        Synthesize narration from script beats, aligned to shot timings.

        Parameters
        ----------
        script_beats:
            Ordered list of narration text segments.
        shot_durations:
            Duration in seconds for each corresponding shot.
        voice_id:
            Provider-specific voice identifier.
        """
