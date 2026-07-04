"""
fal.ai video-generation adapter — Seedance 2.0 Fast (image-to-video).

Image-to-video is a hard contract: ``source_still_url`` is required and
must be non-empty.  Any attempt to call this adapter without a derived still
is rejected immediately, mirroring the mock enforcement.

Model ID (verified 2026-07-03):
  bytedance/seedance-2.0/fast/image-to-video
  $0.2419/sec, lower latency than standard tier.
"""

from __future__ import annotations

import fal_client

from adapters import _cache
from adapters.video_gen.base import VideoGenAdapter, VideoGenResult

_DEFAULT_MODEL = "bytedance/seedance-2.0/fast/image-to-video"

# Seedance supports durations 4–15 s (as strings) or "auto".
_MIN_DURATION = 4
_MAX_DURATION = 15


def _duration_str(seconds: float) -> str:
    """Convert a float duration to the string enum Seedance expects."""
    rounded = int(round(seconds))
    if _MIN_DURATION <= rounded <= _MAX_DURATION:
        return str(rounded)
    return "auto"


class FalVideoGenAdapter(VideoGenAdapter):
    """
    Thin fal.ai wrapper for Seedance 2.0 Fast image-to-video.

    ``FAL_KEY`` must be set in the environment.
    """

    async def generate_clip(
        self,
        source_still_url: str,
        prompt: str,
        duration_seconds: float,
        model: str,
    ) -> VideoGenResult:
        """
        Animate a derived still into a short video clip via Seedance 2.0 Fast.

        Raises
        ------
        ValueError
            If ``source_still_url`` is empty — the still-first invariant is
            enforced here as well as in the graph node.
        RuntimeError
            On any fal.ai API error.
        """
        if not source_still_url:
            raise ValueError(
                "FalVideoGenAdapter.generate_clip requires a non-empty "
                "source_still_url.  A derived still anchored to the character "
                "reference sheet must be provided before video generation."
            )

        # Use the caller-supplied model if it looks like a Seedance endpoint;
        # otherwise fall back to the default.
        endpoint = (
            model
            if model and model.startswith("bytedance/")
            else _DEFAULT_MODEL
        )
        duration = _duration_str(duration_seconds)

        # Cache on the exact request params. This is the most expensive call in
        # the pipeline, so a cache hit here is where the real savings are.
        cache_key = _cache.make_key(
            {
                "endpoint": endpoint,
                "prompt": prompt,
                "source_still_url": source_still_url,
                "duration": duration,
                "resolution": "720p",
            }
        )
        cached = _cache.load("seedance_clip", cache_key)
        if cached is not None:
            return VideoGenResult(
                clip_url=cached["clip_url"],
                duration_seconds=cached["duration_seconds"],
            )

        try:
            result = await fal_client.subscribe_async(
                endpoint,
                arguments={
                    "prompt": prompt,
                    "image_url": source_still_url,
                    "duration": duration,
                    "resolution": "720p",
                    "generate_audio": False,
                },
            )
            clip_url: str = result["video"]["url"]
        except Exception as exc:
            raise RuntimeError(
                f"fal.ai Seedance video generation failed: {exc}"
            ) from exc

        _cache.store(
            "seedance_clip",
            cache_key,
            {"clip_url": clip_url, "duration_seconds": duration_seconds},
        )
        return VideoGenResult(clip_url=clip_url, duration_seconds=duration_seconds)
