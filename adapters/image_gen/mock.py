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
    """

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
    ) -> DerivedStillResult:
        slug = _slugify(shot_prompt)
        url = local_asset_url(f"stills/{slug}_still.png")
        return DerivedStillResult(still_url=url)


def _slugify(text: str) -> str:
    """Convert arbitrary text to a safe lowercase filename fragment."""
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text[:60].strip("_")
