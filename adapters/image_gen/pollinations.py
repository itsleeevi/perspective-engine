"""
Free Pollinations.ai image-generation adapter.

Uses the public Flux endpoint (no API key required) and saves results into
the local asset store. Scene stills are pure text-to-image so environments
match the narration. Requests are serialized + retried on 429.
"""

from __future__ import annotations

import asyncio
import hashlib
import re
import urllib.parse

import httpx

from adapters import _cache
from adapters.image_gen.base import (
    DerivedStillResult,
    ImageGenAdapter,
    ReferenceSheetResult,
)
from graph.assets import save_asset

_ENDPOINT = "https://image.pollinations.ai/prompt/"
_WIDTH = 1280
_HEIGHT = 720
_MODEL = "flux"
_TIMEOUT = 180.0
_MAX_RETRIES = 6

# The public endpoint rate-limits aggressively; one request at a time.
_LOCK = asyncio.Lock()

_STYLE = (
    "flat 2D vector MasterPOV explainer cartoon, bold black outlines, flat cel colors, "
    "soft shading, NOT 3D NOT photoreal, round peach bald head hero, black oval eyes, "
    "red cheek scar, olive hoodie, wide shot showing place and action, high quality, no text"
)


def _slug(text: str) -> str:
    text = re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")
    return text[:50] or "img"


def _shorten(prompt: str, limit: int = 450) -> str:
    prompt = re.sub(r"\s+", " ", prompt).strip()
    if len(prompt) <= limit:
        return prompt
    return prompt[: limit - 1].rsplit(" ", 1)[0] + "…"


async def _generate(prompt: str, seed: int) -> bytes:
    full = _shorten(f"{prompt}. {_STYLE}", 500)
    url = (
        f"{_ENDPOINT}{urllib.parse.quote(full)}"
        f"?width={_WIDTH}&height={_HEIGHT}&model={_MODEL}"
        f"&nologo=true&enhance=true&private=true&seed={seed}"
    )

    last_exc: Exception | None = None
    async with _LOCK:
        for attempt in range(_MAX_RETRIES):
            try:
                async with httpx.AsyncClient(
                    timeout=_TIMEOUT, follow_redirects=True
                ) as client:
                    resp = await client.get(url)
                    if resp.status_code == 429:
                        wait = min(60.0, 2.0**attempt + 1.0)
                        await asyncio.sleep(wait)
                        continue
                    resp.raise_for_status()
                    ctype = resp.headers.get("content-type", "")
                    if not resp.content or "image" not in ctype:
                        raise RuntimeError(
                            f"Pollinations returned non-image content-type={ctype!r}"
                        )
                    # Be polite to the shared free endpoint.
                    await asyncio.sleep(1.2)
                    return resp.content
            except Exception as exc:
                last_exc = exc
                await asyncio.sleep(min(30.0, 1.5 * (attempt + 1)))

    raise RuntimeError(f"Pollinations failed after retries: {last_exc}")


class PollinationsImageGenAdapter(ImageGenAdapter):
    """Free Flux stills via Pollinations — scene-first text-to-image."""

    async def generate_reference_sheet(
        self, character_description: str
    ) -> ReferenceSheetResult:
        cache_key = _cache.make_key(
            {"provider": "pollinations", "role": "ref", "desc": character_description}
        )
        cached = _cache.load("pollinations_ref", cache_key)
        if cached is not None:
            return ReferenceSheetResult(
                image_urls=cached["image_urls"],
                style_descriptor=cached["style_descriptor"],
                cost_usd=0.0,
            )

        prompt = (
            f"{_shorten(character_description, 220)}"
            ", front waist-up portrait, plain cream background, same character sheet look"
        )

        try:
            data = await _generate(prompt, seed=101)
            digest = hashlib.sha1(prompt.encode()).hexdigest()[:10]
            urls = [save_asset(f"refs/pollinations_{digest}.jpg", data)]
        except Exception as exc:
            raise RuntimeError(f"Pollinations reference sheet failed: {exc}") from exc

        style_descriptor = (
            "round peach bald head, black oval eyes, small red right-cheek scar, "
            "bold black outlines, flat colors, dark olive hoodie, explainer-cartoon style"
        )

        _cache.store(
            "pollinations_ref",
            cache_key,
            {"image_urls": urls, "style_descriptor": style_descriptor},
        )

        return ReferenceSheetResult(
            image_urls=urls, style_descriptor=style_descriptor, cost_usd=0.0
        )

    async def derive_still(
        self,
        shot_prompt: str,
        sheet_image_urls: list[str],
        style_descriptor: str,
        attempt: int = 0,
    ) -> DerivedStillResult:
        cache_key = _cache.make_key(
            {
                "provider": "pollinations",
                "role": "still",
                "prompt": shot_prompt,
                "style": style_descriptor,
                "attempt": attempt,
            }
        )
        cached = _cache.load("pollinations_still", cache_key)
        if cached is not None:
            return DerivedStillResult(still_url=cached["still_url"], cost_usd=0.0)

        seed = (
            int(hashlib.sha1(shot_prompt.encode()).hexdigest()[:8], 16) % 1000000
        ) + attempt

        prompt = _shorten(
            f"{shot_prompt}. Look: {style_descriptor}. Full scene, clear setting and action.",
            420,
        )

        try:
            data = await _generate(prompt, seed=seed)
        except Exception as exc:
            raise RuntimeError(f"Pollinations derive_still failed: {exc}") from exc

        digest = hashlib.sha1(shot_prompt.encode()).hexdigest()[:12]
        url = save_asset(f"stills/pollinations_{_slug(shot_prompt)}_{digest}.jpg", data)
        _cache.store("pollinations_still", cache_key, {"still_url": url})
        return DerivedStillResult(still_url=url, cost_usd=0.0)
