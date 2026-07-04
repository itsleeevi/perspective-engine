"""
fal.ai image-generation adapter.

Uses FLUX.1 [dev] for both reference-sheet generation (text-to-image) and
per-shot still derivation (image-to-image with the locked reference sheet).

FLUX.1 [dev] supports reference-image conditioning via its image-to-image
endpoint, satisfying the still-first invariant: every motion shot is derived
from a still anchored to the approved reference sheet.

Model IDs (verified 2026-07-03):
  Text-to-image:   fal-ai/flux/dev
  Image-to-image:  fal-ai/flux/dev/image-to-image
"""

from __future__ import annotations

import os

import fal_client

from adapters import _cache
from adapters.image_gen.base import (
    DerivedStillResult,
    ImageGenAdapter,
    ReferenceSheetResult,
)

_FLUX_T2I = "fal-ai/flux/dev"
_FLUX_I2I = "fal-ai/flux/dev/image-to-image"

# Image size for portrait-style reference stills.
_IMAGE_SIZE = "portrait_4_3"

# Strength of the image-to-image conditioning for derived stills.
# 0.7 = preserve reference identity while adapting to the shot prompt.
_DERIVE_STRENGTH = 0.7


class FalImageGenAdapter(ImageGenAdapter):
    """
    Thin fal.ai wrapper for FLUX.1 [dev] image generation.

    ``FAL_KEY`` must be set in the environment (fal_client picks it up
    automatically from the ``FAL_KEY`` environment variable).
    """

    async def generate_reference_sheet(
        self, character_description: str
    ) -> ReferenceSheetResult:
        """
        Generate three reference images (front, side, three-quarter) via
        FLUX.1 [dev] text-to-image and return their URLs.

        A style_descriptor is derived from the character description and
        includes a deliberately distinctive detail for downstream prompts.
        """
        cache_key = _cache.make_key(
            {
                "model": _FLUX_T2I,
                "description": character_description,
                "image_size": _IMAGE_SIZE,
            }
        )
        cached = _cache.load("flux_reference_sheet", cache_key)
        if cached is not None:
            return ReferenceSheetResult(
                image_urls=cached["image_urls"],
                style_descriptor=cached["style_descriptor"],
            )

        views = [
            ("front view, looking directly at camera", "front"),
            ("side profile view, looking left", "side"),
            ("three-quarter view, slight angle", "three_quarter"),
        ]
        image_urls: list[str] = []
        try:
            for view_prompt, _ in views:
                result = await fal_client.subscribe_async(
                    _FLUX_T2I,
                    arguments={
                        "prompt": (
                            f"{character_description}, {view_prompt}, "
                            "portrait, high quality, detailed, cinematic lighting, "
                            "consistent character appearance"
                        ),
                        "image_size": _IMAGE_SIZE,
                        "num_inference_steps": 28,
                        "num_images": 1,
                    },
                )
                image_urls.append(result["images"][0]["url"])
        except Exception as exc:
            raise RuntimeError(
                f"fal.ai generate_reference_sheet failed: {exc}"
            ) from exc

        style_descriptor = (
            f"{character_description.strip()}. "
            "Distinctive detail: glowing amber left eye. "
            "Consistent across all angles and lighting conditions."
        )
        _cache.store(
            "flux_reference_sheet",
            cache_key,
            {"image_urls": image_urls, "style_descriptor": style_descriptor},
        )
        return ReferenceSheetResult(
            image_urls=image_urls, style_descriptor=style_descriptor
        )

    async def derive_still(
        self,
        shot_prompt: str,
        sheet_image_urls: list[str],
        style_descriptor: str,
    ) -> DerivedStillResult:
        """
        Derive a per-shot still from the reference sheet using FLUX.1 [dev]
        image-to-image, conditioning on the first reference sheet image.

        The result is anchored to the locked character identity.
        """
        if not sheet_image_urls:
            raise RuntimeError(
                "derive_still requires at least one sheet_image_url — "
                "no reference sheet has been generated yet."
            )
        reference_url = sheet_image_urls[0]

        cache_key = _cache.make_key(
            {
                "model": _FLUX_I2I,
                "prompt": shot_prompt,
                "reference_url": reference_url,
                "strength": _DERIVE_STRENGTH,
                "style_descriptor": style_descriptor,
            }
        )
        cached = _cache.load("flux_derive_still", cache_key)
        if cached is not None:
            return DerivedStillResult(still_url=cached["still_url"])

        try:
            result = await fal_client.subscribe_async(
                _FLUX_I2I,
                arguments={
                    "prompt": (
                        f"{shot_prompt}. {style_descriptor}. "
                        "Maintain character identity consistent with the reference image."
                    ),
                    "image_url": reference_url,
                    "strength": _DERIVE_STRENGTH,
                    "num_inference_steps": 28,
                    "num_images": 1,
                },
            )
            still_url: str = result["images"][0]["url"]
        except Exception as exc:
            raise RuntimeError(
                f"fal.ai derive_still failed: {exc}"
            ) from exc

        _cache.store("flux_derive_still", cache_key, {"still_url": still_url})
        return DerivedStillResult(still_url=still_url)
