"""
Gemini 3.1 Flash Image adapter — Nano Banana 2.

Public name: Nano Banana 2. Model id: ``gemini-3.1-flash-image``.
Native 16:9 at 512 / 1K / 2K / 4K, up to 14 reference images per call.

Graph path: ``GeminiImageGenAdapter`` via ``--image-provider gemini-3.1-flash-image``
(aliases ``nano-banana-2``). Documentary path: ``python -m channel images``.
Uses ``GEMINI_API_KEY`` (same key as Gemini TTS). Does not call Google Flow,
fal.ai, or OpenAI Images.
"""

from __future__ import annotations

import asyncio
import base64
import hashlib
import os
import random
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

import httpx

from adapters import _cache, pricing
from adapters.image_gen.base import (
    DerivedStillResult,
    ImageGenAdapter,
    ReferenceSheetResult,
)
from graph import style
from graph.assets import save_asset

GEMINI_IMAGE_MODEL = "gemini-3.1-flash-image"
GEMINI_IMAGE_PUBLIC_NAME = "Nano Banana 2"
GEMINI_IMAGE_ASPECT = "16:9"
GEMINI_IMAGE_SIZE = "2K"
GEMINI_IMAGE_SIZES = ("512", "1K", "2K", "4K")
GEMINI_IMAGE_ASPECTS = (
    "1:1",
    "3:2",
    "2:3",
    "3:4",
    "4:3",
    "4:5",
    "5:4",
    "9:16",
    "16:9",
    "21:9",
    "9:21",
    "1:4",
    "4:1",
    "1:8",
    "8:1",
)
MAX_REFERENCE_IMAGES = 14

_API_HOST = "https://generativelanguage.googleapis.com/v1beta/models"
_MAX_RETRIES = 6
_RETRY_BASE_SECONDS = 2.0
_RETRY_MAX_SECONDS = 60.0
_TIMEOUT = 300.0
_MIME_BY_SUFFIX = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".heic": "image/heic",
    ".heif": "image/heif",
}

# Restate the no-invented-lettering rule at the end of graph prompts.
_TEXT_GUIDANCE_SUFFIX = (
    " Render only the words the scene explicitly asks for. Leave every other "
    "surface in the frame wordless — no invented signs, labels, titles, or "
    "screen text."
)
_REF_PREFIX = (
    "Match the cartoon identity in the attached reference images. Keep that "
    "exact face, hair, and clothes. Draw the scene described; do not copy a "
    "portrait composition onto a wide shot. "
)


class GeminiImageError(RuntimeError):
    """Nano Banana 2 / Gemini image generation failed. Do not swap providers."""


@dataclass
class GeminiImageResult:
    """One generated still plus billed usage."""

    data: bytes
    mime: str = "image/png"
    cost_usd: float = 0.0
    usage: dict[str, Any] = field(default_factory=dict)


def gemini_image_api_key() -> str:
    return (
        os.environ.get("GEMINI_API_KEY", "").strip()
        or os.environ.get("GOOGLE_API_KEY", "").strip()
        or os.environ.get("GOOGLE_GENAI_API_KEY", "").strip()
    )


def image_endpoint(model: str = GEMINI_IMAGE_MODEL) -> str:
    return f"{_API_HOST}/{model}:generateContent"


def mime_for(path: Path | str) -> str:
    suffix = Path(path).suffix.lower()
    return _MIME_BY_SUFFIX.get(suffix, "image/png")


def read_local_image(url_or_path: str) -> tuple[bytes, str] | None:
    """Load a local still from a file:// URL or filesystem path."""
    raw = (url_or_path or "").strip()
    if not raw:
        return None
    if raw.startswith("file:"):
        parsed = urlparse(raw)
        path = Path(unquote(parsed.path))
    else:
        path = Path(raw)
    if not path.is_file() or path.stat().st_size <= 0:
        return None
    return path.read_bytes(), mime_for(path)


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")[:60]


def _digest(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:10]


def _inline_image(payload: dict) -> tuple[bytes, str]:
    try:
        candidate = payload["candidates"][0]
        parts = candidate["content"]["parts"]
        # Thinking models may emit extra parts; the last image is the still.
        inline = None
        for part in parts:
            blob = part.get("inlineData") or part.get("inline_data")
            if blob and blob.get("data"):
                inline = blob
        if not inline or not inline.get("data"):
            raise KeyError("inlineData")
        mime = str(inline.get("mimeType") or inline.get("mime_type") or "image/png")
        return base64.b64decode(inline["data"]), mime
    except (KeyError, IndexError, TypeError, ValueError) as exc:
        err = payload.get("error") or payload.get("promptFeedback") or payload
        raise GeminiImageError(f"Gemini image response had no image: {err!r}") from exc


def _count_modality(details: list[Any], modality: str) -> int:
    total = 0
    needle = modality.upper()
    for item in details:
        if not isinstance(item, dict):
            continue
        mod = str(item.get("modality") or "").upper()
        n = int(item.get("tokenCount") or item.get("token_count") or 0)
        if mod == needle:
            total += n
    return total


def usage_cost(payload: dict, image_size: str) -> tuple[float, dict[str, Any]]:
    """Bill from usageMetadata when present; else the published size floor."""
    usage = payload.get("usageMetadata") or payload.get("usage_metadata") or {}
    details_in = usage.get("promptTokensDetails") or usage.get("prompt_tokens_details") or []
    details_out = (
        usage.get("candidatesTokensDetails") or usage.get("candidates_tokens_details") or []
    )
    thoughts = int(usage.get("thoughtsTokenCount") or usage.get("thoughts_token_count") or 0)
    text_in = _count_modality(details_in, "TEXT")
    image_in = _count_modality(details_in, "IMAGE")
    if not details_in:
        text_in = int(usage.get("promptTokenCount") or usage.get("prompt_token_count") or 0)
    text_out = thoughts + _count_modality(details_out, "TEXT")
    image_out = _count_modality(details_out, "IMAGE")
    if image_out <= 0:
        image_out = pricing.GEMINI_FLASH_IMAGE_OUTPUT_TOKENS.get(
            image_size, pricing.GEMINI_FLASH_IMAGE_OUTPUT_TOKENS["2K"]
        )
    cost = pricing.gemini_flash_image_cost(text_in, image_in, text_out, image_out)
    summary = {
        "text_input_tokens": text_in,
        "image_input_tokens": image_in,
        "text_output_tokens": text_out,
        "image_output_tokens": image_out,
        "image_size": image_size,
    }
    return cost, summary


def _generation_config(aspect_ratio: str, image_size: str) -> dict[str, Any]:
    # Typed ImageConfig (Java/Go/C#) plus REST responseFormat.image used in
    # Google's own gemini-3.1-flash-image examples. Unknown keys are ignored.
    image = {"aspectRatio": aspect_ratio, "imageSize": image_size}
    return {
        "responseModalities": ["TEXT", "IMAGE"],
        "imageConfig": image,
        "responseFormat": {"image": image},
    }


def generate_image(
    prompt: str,
    *,
    api_key: str,
    model: str = GEMINI_IMAGE_MODEL,
    aspect_ratio: str = GEMINI_IMAGE_ASPECT,
    image_size: str = GEMINI_IMAGE_SIZE,
    reference_images: list[tuple[bytes, str]] | None = None,
    client: httpx.Client | None = None,
    timeout: float = _TIMEOUT,
    retries: int = _MAX_RETRIES,
) -> GeminiImageResult:
    """Call Nano Banana 2 and return PNG/JPEG bytes.

    ``reference_images`` is ``(bytes, mime)`` pairs, photo then cartoon sheet,
    capped at 14. Empty prompt or missing key fail closed — no provider swap.
    """
    if not api_key:
        raise GeminiImageError(
            "GEMINI_API_KEY (or GOOGLE_API_KEY) is missing. "
            "Operator Google Flow ingest still works. "
            "Do not fall back to fal.ai, OpenAI Images, or Pollinations."
        )
    text = (prompt or "").strip()
    if not text:
        raise GeminiImageError("empty image prompt")
    if aspect_ratio not in GEMINI_IMAGE_ASPECTS:
        raise GeminiImageError(f"unsupported aspect ratio {aspect_ratio!r}")
    if image_size not in GEMINI_IMAGE_SIZES:
        raise GeminiImageError(
            f"unsupported imageSize {image_size!r}; need one of {GEMINI_IMAGE_SIZES}"
        )

    parts: list[dict[str, Any]] = [{"text": text}]
    for data, mime in (reference_images or [])[:MAX_REFERENCE_IMAGES]:
        if not data:
            continue
        parts.append(
            {
                "inlineData": {
                    "mimeType": mime or "image/png",
                    "data": base64.b64encode(data).decode("ascii"),
                }
            }
        )
    body = {
        "contents": [{"role": "user", "parts": parts}],
        "generationConfig": _generation_config(aspect_ratio, image_size),
    }
    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": api_key,
    }
    url = image_endpoint(model)
    own_client = client is None
    http = client or httpx.Client(timeout=timeout)
    last_error = ""
    try:
        delay = _RETRY_BASE_SECONDS
        for attempt in range(retries):
            response = http.post(url, headers=headers, json=body)
            if response.status_code in {429, 500, 503} and attempt + 1 < retries:
                last_error = response.text[:800]
                time.sleep(delay + random.uniform(0, 0.5))
                delay = min(delay * 2, _RETRY_MAX_SECONDS)
                continue
            if response.status_code >= 400:
                raise GeminiImageError(
                    f"Gemini image HTTP {response.status_code}: {response.text[:800]}"
                )
            payload = response.json()
            data, mime = _inline_image(payload)
            if not data:
                raise GeminiImageError("Gemini image returned empty bytes")
            cost, usage = usage_cost(payload, image_size)
            return GeminiImageResult(data=data, mime=mime, cost_usd=cost, usage=usage)
    finally:
        if own_client:
            http.close()
    raise GeminiImageError(last_error or "Gemini image failed after retries")


class GeminiImageGenAdapter(ImageGenAdapter):
    """
    Nano Banana 2 wrapper matching the ``ImageGenAdapter`` contract.

    ``GEMINI_API_KEY`` must be set. Frames land in the local asset store so
    an assembled video never depends on a provider CDN. Native 16:9, so stills
    are not center-cropped the way gpt-image 3:2 frames are.
    """

    def __init__(
        self,
        model: str = GEMINI_IMAGE_MODEL,
        aspect_ratio: str = GEMINI_IMAGE_ASPECT,
        image_size: str = GEMINI_IMAGE_SIZE,
        api_key: str | None = None,
        client: httpx.Client | None = None,
    ):
        self.model = model
        self.aspect_ratio = aspect_ratio
        self.image_size = image_size
        self._api_key = api_key if api_key is not None else gemini_image_api_key()
        self._client = client

    def _prompt(self, text: str, *, with_refs: bool) -> str:
        prefix = _REF_PREFIX if with_refs else ""
        return prefix + text + _TEXT_GUIDANCE_SUFFIX

    async def _render(
        self,
        prompt: str,
        reference_images: list[tuple[bytes, str]] | None = None,
    ) -> GeminiImageResult:
        return await asyncio.to_thread(
            generate_image,
            prompt,
            api_key=self._api_key,
            model=self.model,
            aspect_ratio=self.aspect_ratio,
            image_size=self.image_size,
            reference_images=reference_images,
            client=self._client,
        )

    async def generate_reference_sheet(
        self, character_description: str
    ) -> ReferenceSheetResult:
        prompt = self._prompt(style.reference_sheet_prompt(character_description), with_refs=False)
        cache_key = _cache.make_key(
            {
                "provider": "gemini",
                "model": self.model,
                "role": "ref",
                "prompt_version": 1,
                "prompt": prompt,
                "aspect": self.aspect_ratio,
                "image_size": self.image_size,
            }
        )
        cached = _cache.load("gemini_reference_sheet", cache_key)
        if cached is not None:
            return ReferenceSheetResult(
                image_urls=cached["image_urls"],
                style_descriptor=cached["style_descriptor"],
                cost_usd=0.0,
            )

        result = await self._render(prompt)
        url = save_asset(
            f"refs/gemini_hero_sheet_{_digest(prompt)}.png",
            result.data,
        )
        _cache.store(
            "gemini_reference_sheet",
            cache_key,
            {"image_urls": [url], "style_descriptor": style.STYLE_DESCRIPTOR},
        )
        return ReferenceSheetResult(
            image_urls=[url],
            style_descriptor=style.STYLE_DESCRIPTOR,
            cost_usd=result.cost_usd,
        )

    async def derive_still(
        self,
        shot_prompt: str,
        sheet_image_urls: list[str],
        style_descriptor: str,
        attempt: int = 0,
    ) -> DerivedStillResult:
        if not sheet_image_urls:
            raise RuntimeError(
                "derive_still requires at least one sheet_image_url — "
                "no reference sheet has been generated yet."
            )
        refs = [
            loaded
            for url in sheet_image_urls
            if (loaded := read_local_image(url)) is not None
        ]
        prompt = self._prompt(shot_prompt, with_refs=bool(refs))
        cache_key = _cache.make_key(
            {
                "provider": "gemini",
                "model": self.model,
                "role": "still",
                "prompt_version": 1,
                "prompt": prompt,
                "aspect": self.aspect_ratio,
                "image_size": self.image_size,
                "attempt": attempt,
                "n_refs": len(refs),
                "ref_sha": [
                    hashlib.sha1(data).hexdigest()[:12] for data, _mime in refs
                ],
            }
        )
        cached = _cache.load("gemini_derive_still", cache_key)
        if cached is not None:
            return DerivedStillResult(still_url=cached["still_url"], cost_usd=0.0)

        result = await self._render(prompt, refs or None)
        still_url = save_asset(
            f"stills/gemini_{_slug(shot_prompt)}_{_digest(shot_prompt)}_{attempt}.png",
            result.data,
        )
        _cache.store("gemini_derive_still", cache_key, {"still_url": still_url})
        return DerivedStillResult(still_url=still_url, cost_usd=result.cost_usd)
