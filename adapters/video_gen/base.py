"""
Base interface for video-generation adapters.

Image-to-video capability is a hard requirement: no adapter may accept a
text prompt without a source still image.  This interface enforces that
contract at the signature level (source_still_url is required, not optional).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class VideoGenResult:
    """Output of a video-generation call."""

    clip_url: str
    """URL of the generated video clip."""
    duration_seconds: float


class VideoGenAdapter(ABC):
    """Abstract video-generation adapter (image-to-video only)."""

    @abstractmethod
    async def generate_clip(
        self,
        source_still_url: str,
        prompt: str,
        duration_seconds: float,
        model: str,
    ) -> VideoGenResult:
        """
        Animate a still image into a short video clip.

        Parameters
        ----------
        source_still_url:
            Required. URL of the per-shot derived still anchored to the
            character reference sheet.  An empty string is rejected.
        prompt:
            Shot-level motion/scene description.
        duration_seconds:
            Target clip duration.
        model:
            Provider model identifier for this shot.
        """
