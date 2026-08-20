"""
OpenAI image-generation adapter — the production image path for this format.

Uses gpt-image-2 at "low" quality. Chosen empirically on 2026-08-16 over
gpt-image-1-mini (the previous default) by generating the same three briefs
through both, including the two cases this format actually fails on:

*Text fidelity.* An in-scene document with four short labels came back from
mini as "APPLICATION FORM / MENE / UDUCATION / WORK HISTORY" — two of four
garbled. gpt-image-2 rendered all four correctly, plus every incidental
string it invented for the background (a to-do list, book spines, a wall
clock), and on a separate brief rendered a full sentence of legal copy
letter-perfect. Short in-scene text is a deliberate storytelling device in
this style, so this is the difference between a usable frame and a reshoot.

*Environment density.* gpt-image-2 fills the frame with the concrete,
narration-relevant clutter the reference format is built on, where mini
tends toward a sparse hero prop on an empty surface.

*Quality tier: low, not medium.* All three tiers were probed on the same
office brief at 1536x1024: low $0.0055, medium $0.0420, high $0.1654 per
image — medium is 7.6x the cost of low. Medium was tried as the default for
a day on the strength of one probe (a US flag whose star grid low rendered
too coarsely), but the failures that actually showed up in a full render —
a duration illustrated as a clock face, a flag whose star count was simply
wrong, a two-word quoted label losing a letter, a bystander drawn
realistically instead of on-model — turned out to be storyboard-prompt and
cast-consistency bugs, not rendering-fidelity ones; the letter-dropping typo
reproduced at medium quality too. Fixing those (see
``adapters/llm/anthropic.py``'s ``_visualize_chunk`` and
``graph/style.py``'s ``CAST_RULE``) closed the gap medium's cost was buying
almost nothing against. High is not viable at any budget: it drifts
off-model, giving the hero a rendered nose and brow the locked design does
not have.

At ~130 shots for a 10-minute video that is $0.72 at low against $5.46 at
medium — the dominant line item in a run's cost either way. Pass
``quality="medium"`` only if a specific scene's real-world detail still
reads wrong at low after the prompt is fixed; it should not be the default
lever for a text or continuity problem.

gpt-image models have no native 16:9 size, so the closest offered landscape
size (1536x1024, 3:2) is used and cropped to 16:9 downstream.

``moderation="low"`` is passed on every call: this format's scripts describe
interrogation, black-site detention, and similar dark-but-abstracted content
by design (see ``LLMAdapter.visualize_beats``, which already renders such
beats as non-graphic symbolic scenes), and the default "auto" moderation
tier refuses some of those prompts outright. Verified empirically against
the darkest beats in ``fixtures/cia_black_ops.json`` (stress positions,
waterboarding, a botched airstrike) before shipping this adapter — all
generated successfully under "low".

No seed parameter exists in this API (unlike fal FLUX), so re-running the
same prompt is not reproducible pixel-for-pixel; the disk cache is what
makes a rerun of the same shot free and stable, same as every other adapter.
"""

from __future__ import annotations

import asyncio
import base64
import hashlib
import io
import random
import re

from openai import AsyncOpenAI, OpenAIError, RateLimitError
from PIL import Image

from adapters import _cache, pricing
from adapters.image_gen.base import (
    DerivedStillResult,
    ImageGenAdapter,
    ReferenceSheetResult,
)
from graph import style
from graph.assets import save_asset

_MODEL = "gpt-image-2"
_QUALITY = "low"
_SIZE = "1536x1024"  # closest offered landscape size; no native 16:9.
_MODERATION = "low"

# Rolling per-minute image quota backoff. The observed account limit is 20
# images/minute, so a full shot list of ~120 will sit behind it repeatedly;
# the ceiling is above a minute to let a saturated window drain completely.
_MAX_RETRIES = 8
_RETRY_BASE_SECONDS = 4.0
_RETRY_MAX_SECONDS = 90.0

# Restates graph.style.TEXT_RULE's key constraint at the very end of the
# prompt, where models weight instructions most heavily. Worth the
# duplication: unrequested background lettering is where every observed
# misspelling came from, and it is the one failure the quality gate cannot
# reliably catch.
_TEXT_GUIDANCE_SUFFIX = (
    " Render only the words the scene explicitly asks for. Leave every other "
    "surface in the frame wordless — no invented signs, labels, titles, or "
    "screen text."
)


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")[:60]


def _digest(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:10]


def _crop_to_16_9(data: bytes) -> bytes:
    """
    Center-crop a landscape image to exactly 16:9.

    gpt-image models have no native 16:9 output size; the closest offered
    size (1536x1024, i.e. 3:2) is narrower-feeling than 16:9, and letting
    ``assemble``'s scale+pad step handle the mismatch would pillarbox every
    OpenAI-sourced shot with black bars fal's native-16:9 stills never have.
    3:2 is *taller* relative to its width than 16:9, so getting to 16:9 means
    trimming a modest strip off the top and bottom, not the sides — no loss
    of the framing that actually matters (the subject is never near the top
    or bottom edge per the style prompt's own framing rules).
    """
    with Image.open(io.BytesIO(data)) as img:
        img = img.convert("RGB")
        width, height = img.size
        target_height = round(width * 9 / 16)
        if target_height >= height:
            return data  # already <=16:9 tall; nothing to trim
        top = (height - target_height) // 2
        cropped = img.crop((0, top, width, top + target_height))
        buf = io.BytesIO()
        cropped.save(buf, format="PNG")
        return buf.getvalue()


class OpenAIImageGenAdapter(ImageGenAdapter):
    """
    gpt-image wrapper, matching the ``ImageGenAdapter`` contract.

    ``OPENAI_API_KEY`` must be set in the environment (the SDK reads it
    directly). Generated frames are copied into the local asset store, same
    as every other image adapter, so an assembled video never depends on a
    provider's own CDN retention.
    """

    def __init__(
        self, model: str = _MODEL, quality: str = _QUALITY, size: str = _SIZE
    ):
        self.model = model
        self.quality = quality
        self.size = size
        self._client = AsyncOpenAI()

    @staticmethod
    def _is_out_of_credit(exc: RateLimitError) -> bool:
        code = getattr(exc, "code", "") or ""
        body = getattr(exc, "body", None)
        if isinstance(body, dict):
            error = body.get("error") or {}
            code = error.get("code") or error.get("type") or code
        return code in {"insufficient_quota", "credit_balance_exhausted"}

    async def _generate_with_backoff(self, prompt: str):
        """
        Call the images API, waiting out per-minute rate limits.

        The account's image limit is a rolling per-minute quota, so a 429 here
        means "too many at once", not "over budget" — the shot list is a fixed
        size and will finish, just not this second. Retrying is the difference
        between a video that takes a few minutes longer and a run that dies
        two thirds of the way through with everything after it unrendered.
        Non-rate-limit errors still fail immediately.
        """
        delay = _RETRY_BASE_SECONDS
        for attempt in range(_MAX_RETRIES):
            try:
                return await self._client.images.generate(
                    model=self.model,
                    prompt=prompt + _TEXT_GUIDANCE_SUFFIX,
                    size=self.size,
                    quality=self.quality,
                    moderation=_MODERATION,
                    n=1,
                )
            except RateLimitError as exc:
                # A spent credit balance is also delivered as a 429, and no
                # amount of waiting fixes it. Retrying it burns eight backoff
                # sleeps and then reports a rate limit, which sends whoever
                # reads the traceback looking for a concurrency bug instead of
                # at the billing page.
                if self._is_out_of_credit(exc):
                    raise RuntimeError(
                        "OpenAI image generation stopped: the account is out "
                        "of credit. Renders already completed are cached, so "
                        "topping up and re-running resumes where this left "
                        f"off. ({exc})"
                    ) from exc
                if attempt == _MAX_RETRIES - 1:
                    raise
                await asyncio.sleep(delay + random.uniform(0, 1.0))
                delay = min(delay * 2, _RETRY_MAX_SECONDS)
            except OpenAIError as exc:
                raise RuntimeError(
                    f"OpenAI gpt-image generation failed: {exc}"
                ) from exc
        raise RuntimeError("unreachable")

    async def _generate(self, prompt: str) -> tuple[bytes, float]:
        try:
            response = await self._generate_with_backoff(prompt)
        except RateLimitError as exc:
            raise RuntimeError(
                f"OpenAI gpt-image rate limit persisted across "
                f"{_MAX_RETRIES} retries: {exc}"
            ) from exc

        item = response.data[0]
        if not item.b64_json:
            raise RuntimeError("OpenAI gpt-image returned no image data.")
        data = _crop_to_16_9(base64.b64decode(item.b64_json))

        usage = response.usage
        cost_usd = (
            pricing.gpt_image_cost(
                model=self.model,
                text_input_tokens=usage.input_tokens_details.text_tokens,
                image_input_tokens=usage.input_tokens_details.image_tokens,
                image_output_tokens=usage.output_tokens_details.image_tokens,
            )
            if usage is not None
            else 0.0
        )
        return data, cost_usd

    async def generate_reference_sheet(
        self, character_description: str
    ) -> ReferenceSheetResult:
        prompt = style.reference_sheet_prompt(character_description)
        cache_key = _cache.make_key(
            {
                "provider": "openai",
                "model": self.model,
                "role": "ref",
                "prompt_version": 5,  # see derive_still's cache_key for why
                "prompt": prompt,
                "size": self.size,
                "quality": self.quality,
            }
        )
        cached = _cache.load("openai_reference_sheet", cache_key)
        if cached is not None:
            # A cache hit makes no new API call, so this run spends $0 here.
            return ReferenceSheetResult(
                image_urls=cached["image_urls"],
                style_descriptor=cached["style_descriptor"],
                cost_usd=0.0,
            )

        data, cost_usd = await self._generate(prompt)
        url = save_asset(f"refs/openai_hero_sheet_{_digest(prompt)}.png", data)

        _cache.store(
            "openai_reference_sheet",
            cache_key,
            {"image_urls": [url], "style_descriptor": style.STYLE_DESCRIPTOR},
        )
        return ReferenceSheetResult(
            image_urls=[url], style_descriptor=style.STYLE_DESCRIPTOR, cost_usd=cost_usd
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

        cache_key = _cache.make_key(
            {
                "provider": "openai",
                "model": self.model,
                "role": "still",
                # Bump when anything appended to the prompt inside _generate
                # changes, or when graph.style's STYLE_BLOCK/HERO_LOOK change
                # meaningfully, so a fix doesn't silently keep serving a
                # stale cached image generated under the old style.
                "prompt_version": 5,
                "prompt": shot_prompt,
                "size": self.size,
                "quality": self.quality,
                "attempt": attempt,
            }
        )
        cached = _cache.load("openai_derive_still", cache_key)
        if cached is not None:
            # A cache hit makes no new API call, so this run spends $0 here.
            return DerivedStillResult(still_url=cached["still_url"], cost_usd=0.0)

        data, cost_usd = await self._generate(shot_prompt)
        still_url = save_asset(
            f"stills/openai_{_slug(shot_prompt)}_{_digest(shot_prompt)}_{attempt}.png",
            data,
        )

        _cache.store("openai_derive_still", cache_key, {"still_url": still_url})
        return DerivedStillResult(still_url=still_url, cost_usd=cost_usd)
