"""
Anthropic Claude LLM adapter.

Uses claude-haiku-4-5-20251001 (cheapest/fastest current model) for all
three LLM roles: script writing, shot breakdown, and quality gate checks.

Disposable adapter — swap model or provider without touching graph/.
"""

from __future__ import annotations

import base64
import json
import os
import re

import anthropic
import httpx

from adapters import _cache
from adapters.llm.base import (
    LLMAdapter,
    QualityCheckResult,
    ScriptResult,
    ShotBreakdownResult,
)

DEFAULT_MODEL = "claude-haiku-4-5-20251001"
_VIDEO_MODEL_SLUG = "bytedance/seedance-2.0/fast/image-to-video"

# Bounded timeout for fetching media ourselves, so Anthropic never has to do a
# (frequently slow / timing-out) server-side download of fal.ai URLs.
_IMAGE_FETCH_TIMEOUT_S = 20.0
_SUPPORTED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}


def _extract_json(text: str) -> str:
    """Strip markdown code fences from Claude's response if present."""
    match = re.search(r"```(?:json)?\s*([\s\S]+?)\s*```", text)
    if match:
        return match.group(1)
    return text.strip()


async def _fetch_image_block(url: str) -> dict | None:
    """
    Download an image and return a base64 Anthropic image content block.

    Returns None if the URL is not fetchable or is not a supported image type
    (e.g. a video clip URL), so the caller can degrade to a text-only check
    rather than failing the whole run.
    """
    if not url.startswith("https://"):
        return None
    try:
        async with httpx.AsyncClient(timeout=_IMAGE_FETCH_TIMEOUT_S) as client:
            resp = await client.get(url, follow_redirects=True)
            resp.raise_for_status()
    except (httpx.HTTPError, httpx.TimeoutException):
        return None

    media_type = resp.headers.get("content-type", "").split(";")[0].strip().lower()
    if media_type not in _SUPPORTED_IMAGE_TYPES:
        return None

    return {
        "type": "image",
        "source": {
            "type": "base64",
            "media_type": media_type,
            "data": base64.standard_b64encode(resp.content).decode("ascii"),
        },
    }


class AnthropicLLMAdapter(LLMAdapter):
    """
    Thin wrapper around the Anthropic Messages API.

    All provider-specific exceptions are re-raised as RuntimeError so the
    graph retry logic receives a plain exception type.
    """

    def __init__(self, model: str = DEFAULT_MODEL) -> None:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        self._client = anthropic.AsyncAnthropic(api_key=api_key)
        self._model = model

    async def write_script(self, topic: str, brief: str) -> ScriptResult:
        prompt = (
            f"Write a 5-beat narrative script for a short video about: {topic}\n\n"
            f"Brief: {brief}\n\n"
            "Rules:\n"
            "- The entire script is told in FIRST PERSON from the perspective of the "
            "main subject/hero of the story (e.g. if the topic is 'a photon's journey' "
            "the narrator IS the photon — 'I was born in the sun's core…').\n"
            "- beats[0] MUST be a punchy first-person hook that immediately drops the "
            "viewer inside the hero's experience.\n"
            "- Each beat advances the hero's journey: origin → challenge → transformation "
            "→ climax → resolution.\n"
            "- Write as vivid, visceral narration — what the hero SEES, FEELS, experiences "
            "moment to moment. Cinematic and sensory.\n"
            "- The hero is a fictional/composite entity — no real, named, identifiable people.\n\n"
            "Return ONLY valid JSON in exactly this format (no extra text):\n"
            '{"beats": ["beat0_hook", "beat1", "beat2", "beat3", "beat4"]}'
        )
        cache_key = _cache.make_key(
            {"role": "write_script", "model": self._model, "topic": topic, "brief": brief}
        )
        cached = _cache.load("anthropic_script", cache_key)
        if cached is not None:
            return ScriptResult(beats=cached["beats"])
        try:
            response = await self._client.messages.create(
                model=self._model,
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = response.content[0].text
            data = json.loads(_extract_json(raw))
            beats: list[str] = data["beats"]
            if not beats:
                raise ValueError("Anthropic returned empty beats list.")
            _cache.store("anthropic_script", cache_key, {"beats": beats})
            return ScriptResult(beats=beats)
        except (anthropic.APIError, anthropic.APIConnectionError) as exc:
            raise RuntimeError(f"Anthropic write_script API error: {exc}") from exc
        except (json.JSONDecodeError, KeyError, ValueError) as exc:
            raise RuntimeError(f"Anthropic write_script parse error: {exc}") from exc

    async def breakdown_shots(
        self, script: list[str], character_descriptor: str
    ) -> ShotBreakdownResult:
        beats_text = "\n".join(f"  [{i}] {b}" for i, b in enumerate(script))
        prompt = (
            "You are a cinematographer turning a first-person narrative script into "
            "a shot list for an AI video generator.\n\n"
            f"Script beats:\n{beats_text}\n\n"
            f"Character descriptor: {character_descriptor}\n\n"
            "Rules:\n"
            f"- ALL shots MUST have mode='motion' and assigned_model='{_VIDEO_MODEL_SLUG}'.\n"
            "- Every shot prompt must be written as an IMMERSIVE FIRST-PERSON POV shot: "
            "the camera IS the hero's eyes. Use language like 'POV:', 'first-person view:', "
            "'seen through the hero's eyes:', 'the hero's perspective looking at…'.\n"
            "- Each prompt must include the character descriptor so visual identity stays "
            "consistent across shots.\n"
            "- Prompts must be vivid and specific: describe what the hero sees, the motion, "
            "the lighting, the environment — NOT what the hero is doing to themselves.\n"
            "- duration_seconds: 5.0 for all shots.\n"
            "- id format: 'shot_000', 'shot_001', etc.\n\n"
            "Return ONLY valid JSON in exactly this format:\n"
            '{"shots": [{"id": "shot_000", "prompt": "...", "duration_seconds": 5.0, '
            '"mode": "motion", "assigned_model": "..."}, ...]}'
        )
        cache_key = _cache.make_key(
            {
                "role": "breakdown_shots",
                "model": self._model,
                "script": script,
                "character_descriptor": character_descriptor,
            }
        )
        cached = _cache.load("anthropic_shots", cache_key)
        if cached is not None:
            return ShotBreakdownResult(
                shots=[
                    ShotBreakdownResult.ShotSpec(**s) for s in cached["shots"]
                ]
            )
        try:
            response = await self._client.messages.create(
                model=self._model,
                max_tokens=2048,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = response.content[0].text
            data = json.loads(_extract_json(raw))
            shots = [
                ShotBreakdownResult.ShotSpec(
                    id=s["id"],
                    prompt=s["prompt"],
                    duration_seconds=float(s.get("duration_seconds", 5.0)),
                    mode=s.get("mode", "static_pan"),
                    assigned_model=s.get("assigned_model", "fal-ai/flux/dev"),
                )
                for s in data["shots"]
            ]
            # Enforce: all shots must be motion (prompt instructs this; guard against drift).
            shots = [
                ShotBreakdownResult.ShotSpec(
                    id=s.id,
                    prompt=s.prompt,
                    duration_seconds=s.duration_seconds,
                    mode="motion",
                    assigned_model=_VIDEO_MODEL_SLUG,
                )
                for s in shots
            ]
            _cache.store(
                "anthropic_shots",
                cache_key,
                {
                    "shots": [
                        {
                            "id": s.id,
                            "prompt": s.prompt,
                            "duration_seconds": s.duration_seconds,
                            "mode": s.mode,
                            "assigned_model": s.assigned_model,
                        }
                        for s in shots
                    ]
                },
            )
            return ShotBreakdownResult(shots=shots)
        except (anthropic.APIError, anthropic.APIConnectionError) as exc:
            raise RuntimeError(f"Anthropic breakdown_shots API error: {exc}") from exc
        except (json.JSONDecodeError, KeyError, ValueError) as exc:
            raise RuntimeError(f"Anthropic breakdown_shots parse error: {exc}") from exc

    async def quality_check(
        self,
        shot_id: str,
        clip_url: str,
        still_url: str,
        style_descriptor: str,
        sheet_image_urls: list[str],
    ) -> QualityCheckResult:
        # Build the vision-capable message by fetching images ourselves and
        # sending them as base64. Passing URLs would make Anthropic's servers
        # fetch the (slow / large) fal.ai media, which times out. Video clip
        # URLs and unfetchable URLs are simply skipped (text-only fallback).
        content: list[dict] = []
        still_block = await _fetch_image_block(still_url)
        if still_block is not None:
            content.append(still_block)
        if sheet_image_urls:
            sheet_block = await _fetch_image_block(sheet_image_urls[0])
            if sheet_block is not None:
                content.append(sheet_block)

        text_part = (
            f"Quality-check shot '{shot_id}'.\n"
            f"Style descriptor: {style_descriptor}\n"
            "Evaluate ONLY for obvious defects — be lenient on minor stylistic differences:\n"
            "1. Is the image severely blurred, corrupted, or completely unrecognisable?\n"
            "2. Is the subject entirely wrong (e.g. a car instead of a person)?\n"
            "3. Are there serious NSFW / safety issues?\n\n"
            "Pass the shot unless at least one of the above is clearly true.\n"
            "Stylistic differences, minor lighting inconsistencies, and imperfect "
            "detail matches are NOT grounds for failure.\n\n"
            "Return ONLY valid JSON:\n"
            '{"passed": true, "failure_reason": ""}\n'
            "Set passed=false ONLY for the obvious defects listed above."
        )
        content.append({"type": "text", "text": text_part})

        try:
            response = await self._client.messages.create(
                model=self._model,
                max_tokens=512,
                messages=[{"role": "user", "content": content}],
            )
            raw = response.content[0].text
            data = json.loads(_extract_json(raw))
            return QualityCheckResult(
                passed=bool(data.get("passed", True)),
                failure_reason=data.get("failure_reason", ""),
            )
        except (anthropic.APIError, anthropic.APIConnectionError) as exc:
            raise RuntimeError(f"Anthropic quality_check API error: {exc}") from exc
        except (json.JSONDecodeError, KeyError) as exc:
            # Fail open on parse errors — let the graph continue.
            return QualityCheckResult(passed=True, failure_reason="")
