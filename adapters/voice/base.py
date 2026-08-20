"""
Base interface for voice / TTS adapters.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class VoiceoverResult:
    """Output of a TTS call."""

    audio_url: str
    """URL of the generated audio file."""
    duration_seconds: float
    """Actual rendered duration."""
    beat_durations: list[float] = field(default_factory=list)
    """
    Measured duration of each narration beat, in the order supplied, including
    any pause the adapter inserts after it. The caller uses these to set each
    shot's on-screen time, so an image change lands exactly on the narration
    boundary instead of on an estimate. Empty if the adapter cannot measure
    per-beat timing.
    """
    cost_usd: float = 0.0
    """Real provider spend for this call. 0.0 for mocks and cache hits."""


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
