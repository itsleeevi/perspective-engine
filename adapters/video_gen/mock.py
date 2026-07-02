"""
Deterministic mock video-generation adapter for Phase 1 (local skeleton).

Enforces the still-first invariant: raises ValueError if source_still_url
is empty, mirroring what a real adapter would reject.
"""

from __future__ import annotations

import re

from adapters.video_gen.base import VideoGenAdapter, VideoGenResult
from graph.assets import local_asset_url


class MockVideoGenAdapter(VideoGenAdapter):
    """
    Stand-in video generator that returns deterministic placeholder URLs.

    Raises ValueError if called without a source still, mirroring the
    still-first invariant enforced by the real adapter contract.
    """

    async def generate_clip(
        self,
        source_still_url: str,
        prompt: str,
        duration_seconds: float,
        model: str,
    ) -> VideoGenResult:
        if not source_still_url:
            raise ValueError(
                "VideoGenAdapter.generate_clip requires a source_still_url. "
                "A derived still anchored to the character reference sheet "
                "must be provided before any video-generation call."
            )
        slug = _slugify(prompt)
        url = local_asset_url(f"clips/{slug}_clip.mp4")
        return VideoGenResult(clip_url=url, duration_seconds=duration_seconds)


def _slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text[:60].strip("_")
