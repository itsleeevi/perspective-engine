"""
fal.ai image-generation adapter.

Uses FLUX.1 [schnell] for both the hero reference sheet and every scene still.
Schnell renders a 2048x1152 frame in 2-3 seconds for ~$0.009, which is what
makes a 100-shot video affordable; its four-step schedule is also well suited
to flat vector art, where there is little fine texture for extra steps to
resolve.

Scene stills are text-to-image, not image-to-image from the reference sheet.
Conditioning a wide establishing shot on a portrait drags the composition back
toward the portrait and collapses the backgrounds this format depends on;
identity is instead held by the locked hero spec that ``graph.style`` stamps
into every prompt, plus a deterministic per-prompt seed.

Model IDs (verified 2026-08-16):
  Text-to-image:   fal-ai/flux/schnell
  Image-to-image:  fal-ai/flux/dev/image-to-image   (motion escape hatch only)
"""

from __future__ import annotations

import hashlib
import io
import re

import fal_client
import httpx
from PIL import Image

from adapters import _cache, pricing
from adapters.image_gen.base import (
    DerivedStillResult,
    ImageGenAdapter,
    ReferenceSheetResult,
)
from graph import style
from graph.assets import save_asset

_FLUX_T2I = "fal-ai/flux/schnell"
_FLUX_I2I = "fal-ai/flux/dev/image-to-image"

# FLUX.1 [schnell] is distilled to four steps; more does not improve output.
_STEPS = 4

_DOWNLOAD_TIMEOUT = 120.0

# fal.ai's schnell endpoint occasionally returns a solid-black frame with no
# API-visible error (observed independent of prompt content, at low but
# nonzero rate). It is cheap and fast enough to detect locally and just
# re-roll, rather than paying for an Anthropic vision call to catch it later
# or shipping a black frame into the final video.
_DEGENERATE_STD_THRESHOLD = 4.0  # stdev of an 8-bit grayscale thumbnail
_MAX_GENERATION_ATTEMPTS = 3
_RETRY_SEED_STRIDE = 7919  # arbitrary prime; keeps re-rolls far apart in seed space


def _seed(text: str) -> int:
    """Stable 31-bit seed from a prompt, so a rerun reproduces the same frame."""
    return int(hashlib.sha256(text.encode("utf-8")).hexdigest()[:8], 16) % (2**31)


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")[:60]


def _is_degenerate(data: bytes) -> bool:
    """True if the image is (near) a single flat colour, i.e. a blank frame."""
    try:
        with Image.open(io.BytesIO(data)) as img:
            pixels = list(img.convert("L").resize((64, 64)).getdata())
    except Exception:
        return True
    mean = sum(pixels) / len(pixels)
    variance = sum((p - mean) ** 2 for p in pixels) / len(pixels)
    return variance**0.5 < _DEGENERATE_STD_THRESHOLD


async def _generate_once(prompt: str, width: int, height: int, seed: int) -> bytes:
    try:
        result = await fal_client.subscribe_async(
            _FLUX_T2I,
            arguments={
                "prompt": prompt,
                "image_size": {"width": width, "height": height},
                "num_inference_steps": _STEPS,
                "num_images": 1,
                "seed": seed,
                "enable_safety_checker": False,
            },
        )
        url = result["images"][0]["url"]
        async with httpx.AsyncClient(timeout=_DOWNLOAD_TIMEOUT) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            return resp.content
    except Exception as exc:
        raise RuntimeError(f"fal.ai FLUX generation failed: {exc}") from exc


async def _generate(prompt: str, width: int, height: int, seed: int | None = None) -> bytes:
    """Render one frame, re-rolling the seed if the result comes back blank."""
    base_seed = _seed(prompt) if seed is None else seed
    data = b""
    for retry in range(_MAX_GENERATION_ATTEMPTS):
        data = await _generate_once(prompt, width, height, base_seed + retry * _RETRY_SEED_STRIDE)
        if not _is_degenerate(data):
            return data
    # Every attempt came back blank; return the last draw and let the
    # shot-level quality gate / retry-and-escalate loop be the backstop.
    return data


class FalImageGenAdapter(ImageGenAdapter):
    """
    Thin fal.ai wrapper for FLUX.1 image generation.

    ``FAL_KEY`` must be set in the environment (fal_client reads it directly).
    Generated frames are copied into the local asset store, so an assembled
    video never depends on fal's CDN retention.
    """

    def __init__(self, width: int = style.GEN_WIDTH, height: int = style.GEN_HEIGHT):
        self.width = width
        self.height = height

    async def generate_reference_sheet(
        self, character_description: str
    ) -> ReferenceSheetResult:
        """
        Generate the hero reference sheet: one full-body front view on a plain
        background, which is what the quality gate compares stills against.
        """
        prompt = style.reference_sheet_prompt(character_description)
        cache_key = _cache.make_key(
            {"model": _FLUX_T2I, "prompt": prompt, "w": self.width, "h": self.height}
        )
        cached = _cache.load("flux_reference_sheet", cache_key)
        if cached is not None:
            # A cache hit makes no new API call, so this run spends $0 here.
            return ReferenceSheetResult(
                image_urls=cached["image_urls"],
                style_descriptor=cached["style_descriptor"],
                cost_usd=0.0,
            )

        data = await _generate(prompt, self.width, self.height)
        url = save_asset(f"refs/hero_sheet_{_seed(prompt):08x}.jpg", data)

        _cache.store(
            "flux_reference_sheet",
            cache_key,
            {"image_urls": [url], "style_descriptor": style.STYLE_DESCRIPTOR},
        )
        return ReferenceSheetResult(
            image_urls=[url],
            style_descriptor=style.STYLE_DESCRIPTOR,
            cost_usd=pricing.flux_schnell_image_cost(self.width, self.height),
        )

    async def derive_still(
        self,
        shot_prompt: str,
        sheet_image_urls: list[str],
        style_descriptor: str,
        attempt: int = 0,
    ) -> DerivedStillResult:
        """
        Render the scene still for one shot.

        ``shot_prompt`` already carries the locked hero spec and style block
        (built by ``graph.style.scene_prompt``), so it is used as-is. The
        attempt index shifts the seed so a retry is a genuinely different draw.
        """
        if not sheet_image_urls:
            raise RuntimeError(
                "derive_still requires at least one sheet_image_url — "
                "no reference sheet has been generated yet."
            )

        cache_key = _cache.make_key(
            {
                "model": _FLUX_T2I,
                "prompt": shot_prompt,
                "w": self.width,
                "h": self.height,
                "attempt": attempt,
            }
        )
        cached = _cache.load("flux_derive_still", cache_key)
        if cached is not None:
            # A cache hit makes no new API call, so this run spends $0 here.
            return DerivedStillResult(still_url=cached["still_url"], cost_usd=0.0)

        seed = _seed(shot_prompt) + attempt
        data = await _generate(shot_prompt, self.width, self.height, seed)
        still_url = save_asset(f"stills/{_slug(shot_prompt)}_{seed:08x}.jpg", data)

        _cache.store("flux_derive_still", cache_key, {"still_url": still_url})
        return DerivedStillResult(
            still_url=still_url,
            cost_usd=pricing.flux_schnell_image_cost(self.width, self.height),
        )
