"""
Anthropic Claude LLM adapter.

Uses claude-haiku-4-5-20251001 (cheapest/fastest current model) for all
three LLM roles: script writing, shot breakdown, and quality gate checks.

Disposable adapter — swap model or provider without touching graph/.
"""

from __future__ import annotations

import asyncio
import base64
import json
import os
import random
import re
from pathlib import Path

import anthropic
import httpx

from adapters import _cache, pricing
from adapters.llm import _prompts
from adapters.llm.base import (
    CHARACTER_FREE_SHOT_TYPES,
    LLMAdapter,
    QualityCheckResult,
    ScriptResult,
    ShotBreakdownResult,
    VisualBeatsResult,
)
from graph.script_fixture import fixture_to_beats

DEFAULT_MODEL = "claude-haiku-4-5-20251001"

# Script writing and storyboarding get a stronger model than the quality gate.
#
# Both are low-volume — one script call and roughly ten storyboard calls for a
# whole video — while the gate runs once per shot with an image attached, so
# the gate is where model choice actually drives cost. Haiku's failures on the
# storyboard were comprehension failures, not style ones: it rendered "the
# entire interview lasts 22 minutes" as a digital clock reading 22:00, in a
# living room, abandoning the interview the surrounding fragments had
# established. Sonnet holds the scene's location across consecutive fragments
# and reads numbers as what they are.
AUTHORING_MODEL = "claude-haiku-4-5-20251001"

# Sonnet 5 was tried here for a day, at 5x Haiku's per-token cost, to fix a
# real comprehension bug: Haiku illustrated "the interview lasts 22 minutes"
# as a clock reading 22:00, abandoning the interview room entirely. That
# turned out to be fixable in the prompt (see the duration/location/flag
# rules in _visualize_chunk below) rather than needing a stronger model, and
# a head-to-head with the patched prompt confirmed it: Haiku followed the
# duration rule correctly on the same fragment, while Sonnet 5 introduced a
# DIFFERENT version of the same bug (a wall clock reading '11:22', reusing
# the duration's own digits). Model tier was never the lever; the explicit
# rule is, and Haiku holds up against it as well as Sonnet 5 does.
# Sonnet-tier models reason before answering unless told not to, and the
# reasoning is not free in either sense: it is billed at the output rate, and
# it competes with the answer for max_tokens. Asked for a script, Sonnet 5
# once spent its entire 8192-token budget thinking and returned a response
# with no text block at all. Both authoring jobs are writing tasks with the
# thinking already done for them by the prompt, so this stays disabled
# regardless of which model is configured. Accepted by every current Claude
# model (including Haiku), so it is always safe to pass.
_NO_THINKING = {"type": "disabled"}

# Backoff for the transient failures of a ~150-call run (see
# ``_create_with_backoff``).
_MAX_RETRIES = 5
_RETRY_BASE_SECONDS = 2.0
_RETRY_MAX_SECONDS = 30.0
_VIDEO_MODEL_SLUG = "bytedance/seedance-2.0/fast/image-to-video"

# Prompt text (shared across every provider adapter) lives in
# adapters.llm._prompts; this assertion still belongs here, next to the one
# adapter still doing its own JSON parsing of the shot_type field.
assert CHARACTER_FREE_SHOT_TYPES <= set(_prompts.SHOT_TYPES)

# Bounded timeout for fetching media ourselves, so Anthropic never has to do a
# (frequently slow / timing-out) server-side download of fal.ai URLs.
_IMAGE_FETCH_TIMEOUT_S = 20.0
_SUPPORTED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}
_EXTENSION_MEDIA_TYPES = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".gif": "image/gif",
    ".webp": "image/webp",
}


async def _create_with_backoff(client, **kwargs):
    """
    Call the messages API, retrying the failures that are about timing.

    A single video makes on the order of 150 calls here, one per shot for the
    quality gate, and connection timeouts and rate limits both show up over a
    run that long. Letting one bubble up kills a pipeline that is most of the
    way through and has already paid for its images. Everything else — a bad
    request, an auth failure, an overlong prompt — is a real error and is
    raised on the first attempt.
    """
    delay = _RETRY_BASE_SECONDS
    for attempt in range(_MAX_RETRIES):
        try:
            return await client.messages.create(**kwargs)
        except (
            anthropic.APITimeoutError,
            anthropic.APIConnectionError,
            anthropic.RateLimitError,
            anthropic.InternalServerError,
        ):
            if attempt == _MAX_RETRIES - 1:
                raise
            await asyncio.sleep(delay + random.uniform(0, 1.0))
            delay = min(delay * 2, _RETRY_MAX_SECONDS)
    raise RuntimeError("unreachable")


def _response_text(response) -> str:
    """
    Join the text blocks of a response, ignoring any others.

    ``response.content[0]`` is not reliably the answer: models that reason
    before replying put a ``thinking`` block first, and reading ``.text`` off
    it raises. Which models do this varies by model and by request, so the
    block type is filtered on rather than assumed.
    """
    text = "".join(
        block.text for block in response.content if getattr(block, "type", "") == "text"
    )
    if not text:
        # Worth naming explicitly. The way this fails otherwise is a JSON
        # decode error on an empty string, which points at the prompt rather
        # than at a response that ran out of tokens before it began replying.
        raise ValueError(
            "response contained no text block "
            f"(stop_reason={response.stop_reason}, "
            f"blocks={[getattr(b, 'type', '?') for b in response.content]})"
        )
    return text


def _extract_json(text: str) -> str:
    """Strip markdown code fences from Claude's response if present."""
    match = re.search(r"```(?:json)?\s*([\s\S]+?)\s*```", text)
    if match:
        return match.group(1)
    return text.strip()


async def _fetch_image_block(url: str) -> dict | None:
    """
    Download an image and return a base64 Anthropic image content block.

    Handles both ``https://`` and the ``file://`` URLs the local asset store
    produces. Returns None if the image is not readable or is not a supported
    image type (e.g. a video clip URL), so the caller can degrade to a
    text-only check rather than failing the whole run.
    """
    if url.startswith("file://"):
        path = Path(url.removeprefix("file://"))
        media_type = _EXTENSION_MEDIA_TYPES.get(path.suffix.lower())
        if media_type is None or not path.is_file():
            return None
        content = path.read_bytes()
    elif url.startswith("https://"):
        try:
            async with httpx.AsyncClient(timeout=_IMAGE_FETCH_TIMEOUT_S) as client:
                resp = await client.get(url, follow_redirects=True)
                resp.raise_for_status()
        except (httpx.HTTPError, httpx.TimeoutException):
            return None
        media_type = resp.headers.get("content-type", "").split(";")[0].strip().lower()
        if media_type not in _SUPPORTED_IMAGE_TYPES:
            return None
        content = resp.content
    else:
        return None

    return {
        "type": "image",
        "source": {
            "type": "base64",
            "media_type": media_type,
            "data": base64.standard_b64encode(content).decode("ascii"),
        },
    }


class AnthropicLLMAdapter(LLMAdapter):
    """
    Thin wrapper around the Anthropic Messages API.

    All provider-specific exceptions are re-raised as RuntimeError so the
    graph retry logic receives a plain exception type.
    """

    def __init__(
        self, model: str = DEFAULT_MODEL, authoring_model: str = AUTHORING_MODEL
    ) -> None:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        self._client = anthropic.AsyncAnthropic(api_key=api_key)
        self._model = model
        self._authoring_model = authoring_model

    async def write_script(
        self,
        topic: str,
        brief: str,
        include_hook: bool = True,
        target_minutes: float = 0.0,
    ) -> ScriptResult:
        """
        Generate a "your life as every level of X" script from a title alone.

        Every fixture in ``fixtures/`` and every real reference video this
        format is modelled on shares one structure: a cold-open hook, then
        8-10 escalating second-person "levels", each with its own short role
        name and a block of narration. The prompt below describes that
        structure so the LLM can produce it for ANY topic, not just the
        hand-authored demo fixtures. The result is fed through the same
        ``fixture_to_beats`` expansion a fixture file goes through, so an
        LLM-written script and a fixture-written script are indistinguishable
        to every downstream node.

        ``target_minutes`` sizes the whole script to a runtime by converting
        it into a word budget at the measured narration rate. Length has to
        be controlled *here*, at the writing step: capping levels afterwards
        would drop the final level, and the final level is the one that
        closes the loop back to the beginning.
        """
        prompt = _prompts.write_script_prompt(topic, brief, target_minutes)
        cache_key = _cache.make_key(
            {
                "role": "write_script",
                "prompt_version": _prompts.WRITE_SCRIPT_PROMPT_VERSION,
                "model": self._authoring_model,
                "topic": topic,
                "brief": brief,
                "include_hook": include_hook,
                "target_minutes": target_minutes,
            }
        )
        cached = _cache.load("anthropic_script", cache_key)
        if cached is not None:
            # A cache hit makes no new API call, so this run spends $0 here.
            return ScriptResult(beats=cached["beats"], cost_usd=0.0)
        try:
            response = await _create_with_backoff(
                self._client,
                model=self._authoring_model,
                max_tokens=8192,
                thinking=_NO_THINKING,
                messages=[{"role": "user", "content": prompt}],
            )
            cost_usd = pricing.claude_cost(
                self._authoring_model,
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens,
            )
            raw = _response_text(response)
            data = json.loads(_extract_json(raw))
            hook = str(data.get("hook", "")).strip()
            raw_levels = data.get("levels")
            if not isinstance(raw_levels, list) or not raw_levels:
                raise ValueError("Anthropic write_script returned no levels.")
            levels: list[dict] = []
            for entry in raw_levels:
                name = str(entry.get("name", "")).strip()
                beats = [
                    str(b).strip() for b in entry.get("beats", []) if str(b).strip()
                ]
                if name and beats:
                    levels.append({"name": name, "beats": beats})
            if not levels:
                raise ValueError("Anthropic write_script returned no usable levels.")
            beats_flat = fixture_to_beats(
                {"hook": hook, "levels": levels}, include_hook=include_hook
            )
            _cache.store("anthropic_script", cache_key, {"beats": beats_flat})
            return ScriptResult(beats=beats_flat, cost_usd=cost_usd)
        except (anthropic.APIError, anthropic.APIConnectionError) as exc:
            raise RuntimeError(f"Anthropic write_script API error: {exc}") from exc
        except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
            raise RuntimeError(f"Anthropic write_script parse error: {exc}") from exc

    async def visualize_beats(
        self, beats: list[str], topic: str = ""
    ) -> VisualBeatsResult:
        """
        Rewrite narration beats as third-person visual scene descriptions.

        Batched in groups so a 100-beat script costs a handful of calls: the
        model also sees neighbouring beats, which keeps consecutive shots from
        describing the same location in different words. Each batch is shown
        the tail of the previous one as read-only context, because otherwise
        the first shot after a batch boundary has no idea where it is and
        reliably relocates the story mid-scene.
        """
        if not beats:
            return VisualBeatsResult(descriptions=[], cost_usd=0.0)

        cache_key = _cache.make_key(
            {
                "role": "visualize_beats",
                "prompt_version": _prompts.VISUALIZE_BEATS_PROMPT_VERSION,
                "model": self._authoring_model,
                "beats": beats,
                "topic": topic,
            }
        )
        cached = _cache.load("anthropic_visual_beats", cache_key)
        if cached is not None:
            # A cache hit makes no new API call, so this run spends $0 here.
            return VisualBeatsResult(
                descriptions=cached["descriptions"],
                shot_types=cached.get("shot_types", []),
                cost_usd=0.0,
            )

        descriptions = [""] * len(beats)
        shot_types = [""] * len(beats)
        cost_usd = 0.0
        for start in range(0, len(beats), _prompts.VISUALIZE_BATCH):
            chunk = beats[start : start + _prompts.VISUALIZE_BATCH]
            lead_in = beats[max(0, start - _prompts.VISUALIZE_LEAD_IN) : start]
            chunk_map, chunk_cost = await self._visualize_chunk(chunk, topic, lead_in)
            for offset, (description, shot_type) in chunk_map.items():
                descriptions[start + offset] = description
                shot_types[start + offset] = shot_type
            cost_usd += chunk_cost

        _cache.store(
            "anthropic_visual_beats",
            cache_key,
            {"descriptions": descriptions, "shot_types": shot_types},
        )
        return VisualBeatsResult(
            descriptions=descriptions, shot_types=shot_types, cost_usd=cost_usd
        )

    async def _visualize_chunk(
        self, beats: list[str], topic: str = "", lead_in: list[str] | None = None
    ) -> tuple[dict[int, tuple[str, str]], float]:
        """
        Visualise one batch, returning ``{beat_index: (description, shot_type)}``.

        Each entry carries the index of the beat it belongs to, so a dropped
        or extra item is simply absent from the map instead of shifting every
        later beat onto the wrong scene. The caller falls back to the local
        rewriter for anything missing.

        ``shot_type`` is returned as its own field rather than left implicit
        in the prose because it decides whether the hero description is
        appended to the image prompt at all (see ``graph.style.scene_prompt``).
        """
        prompt = _prompts.visualize_chunk_prompt(beats, topic, lead_in)
        try:
            response = await _create_with_backoff(
                self._client,
                model=self._authoring_model,
                max_tokens=4096,
                thinking=_NO_THINKING,
                messages=[{"role": "user", "content": prompt}],
            )
            cost_usd = pricing.claude_cost(
                self._authoring_model,
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens,
            )
            data = json.loads(_extract_json(_response_text(response)))
            scenes: dict[int, tuple[str, str]] = {}
            for entry in data["scenes"]:
                index = int(entry["beat"])
                description = str(entry["description"]).strip()
                shot_type = str(entry.get("shot_type", "")).strip().lower()
                if shot_type not in _prompts.SHOT_TYPES:
                    # Unrecognised: fall back to the type that keeps the hero
                    # in the prompt, since a missing character is the more
                    # visible failure of the two.
                    shot_type = "medium shot"
                if 0 <= index < len(beats) and description:
                    scenes[index] = (description, shot_type)
        except (anthropic.APIError, anthropic.APIConnectionError) as exc:
            raise RuntimeError(f"Anthropic visualize_beats API error: {exc}") from exc
        except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
            raise RuntimeError(f"Anthropic visualize_beats parse error: {exc}") from exc

        return scenes, cost_usd

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
            # A cache hit makes no new API call, so this run spends $0 here.
            return ShotBreakdownResult(
                shots=[
                    ShotBreakdownResult.ShotSpec(**s) for s in cached["shots"]
                ],
                cost_usd=0.0,
            )
        try:
            response = await _create_with_backoff(
                self._client,
                model=self._model,
                max_tokens=2048,
                messages=[{"role": "user", "content": prompt}],
            )
            cost_usd = pricing.claude_haiku_cost(
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens,
            )
            raw = _response_text(response)
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
            return ShotBreakdownResult(shots=shots, cost_usd=cost_usd)
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
            "1. Is the image severely blurred, corrupted, blank/solid-colour, or "
            "completely unrecognisable?\n"
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
            response = await _create_with_backoff(
                self._client,
                model=self._model,
                max_tokens=512,
                messages=[{"role": "user", "content": content}],
            )
            cost_usd = pricing.claude_haiku_cost(
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens,
            )
            raw = _response_text(response)
            data = json.loads(_extract_json(raw))
            return QualityCheckResult(
                passed=bool(data.get("passed", True)),
                failure_reason=data.get("failure_reason", ""),
                cost_usd=cost_usd,
            )
        except (anthropic.APIError, anthropic.APIConnectionError) as exc:
            raise RuntimeError(f"Anthropic quality_check API error: {exc}") from exc
        except (json.JSONDecodeError, KeyError) as exc:
            # Fail open on parse errors, but the call itself still spent money.
            cost_usd = pricing.claude_haiku_cost(
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens,
            )
            return QualityCheckResult(passed=True, failure_reason="", cost_usd=cost_usd)
