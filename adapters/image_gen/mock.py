"""
Deterministic mock image-generation adapter for Phase 1 (local skeleton).

Returns stable file:// URLs pointing into a local assets directory.
No images are actually created; the URLs are placeholders used by
downstream nodes and tests to verify the still-first invariant.
"""

from __future__ import annotations

import re

from adapters.image_gen.base import (
    DerivedStillResult,
    ImageGenAdapter,
    ReferenceSheetResult,
)
from graph.assets import local_asset_url


class MockImageGenAdapter(ImageGenAdapter):
    """
    Stand-in image generator that returns deterministic placeholder URLs.

    ``fail_times`` simulates an adapter-level failure (a moderation block, an
    exhausted rate-limit backoff) rather than a quality-gate rejection: it
    raises out of ``derive_still`` itself for the first N calls, so tests can
    exercise the retry/escalate path ``process_shot`` takes around the
    generation call, not just around ``check_quality``.
    """

    def __init__(self, fail_times: int = 0) -> None:
        self._fail_times = fail_times
        self._calls = 0

    async def generate_reference_sheet(
        self, character_description: str
    ) -> ReferenceSheetResult:
        slug = _slugify(character_description)
        urls = [
            local_asset_url(f"refs/{slug}_front.png"),
            local_asset_url(f"refs/{slug}_side.png"),
            local_asset_url(f"refs/{slug}_three_quarter.png"),
        ]
        descriptor = (
            f"{character_description.strip()}. "
            "Distinctive detail: glowing amber left eye. "
            "Consistent across all angles and lighting."
        )
        return ReferenceSheetResult(image_urls=urls, style_descriptor=descriptor)

    async def derive_still(
        self,
        shot_prompt: str,
        sheet_image_urls: list[str],
        style_descriptor: str,
        attempt: int = 0,
    ) -> DerivedStillResult:
        self._calls += 1
        if self._calls <= self._fail_times:
            raise RuntimeError("mock generation failure (e.g. moderation_blocked)")
        slug = _slugify(shot_prompt)
        suffix = "" if attempt == 0 else f"_r{attempt}"
        url = local_asset_url(f"stills/{slug}_still{suffix}.png")
        return DerivedStillResult(still_url=url)


def _slugify(text: str) -> str:
    """Convert arbitrary text to a safe lowercase filename fragment."""
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text[:60].strip("_")
