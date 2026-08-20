"""
OpenAI LLM adapter for the two authoring calls: script writing and
storyboard visualization.

Prompt content for both is shared verbatim with the Anthropic adapter (see
``adapters.llm._prompts``) — the behavioral fixes for this format (duration
vs. clock, cast consistency, flag avoidance, ...) live in the prompt, not in
provider-specific code, so they apply no matter which provider is configured.

The vision-based quality check and the (unused) generic shot-breakdown call
are delegated to an internal ``AnthropicLLMAdapter`` rather than reimplemented
here: they were never the thing being swapped, and Anthropic's Claude Haiku
is already the cheap, adequate choice for a per-shot vision check that runs
~150 times per video (see ``adapters/llm/anthropic.py``).
"""

from __future__ import annotations

import asyncio
import json
import os
import random

from openai import (
    APIConnectionError,
    APIError,
    APITimeoutError,
    AsyncOpenAI,
    InternalServerError,
    RateLimitError,
)

from adapters import _cache, pricing
from adapters.llm import _prompts
from adapters.llm.anthropic import AnthropicLLMAdapter
from adapters.llm.base import (
    LLMAdapter,
    QualityCheckResult,
    ScriptResult,
    ShotBreakdownResult,
    VisualBeatsResult,
)
from graph.script_fixture import fixture_to_beats

# GPT-5.6 Terra: OpenAI's mid tier, priced at $2/$12 per MTok — the closest
# analogue to Claude Sonnet's tier ($2/$10), and the safer first choice for a
# cutover to a provider this codebase hadn't used for authoring before. Luna
# ($0.20/$1.20, Haiku's analogue) is worth probing the same way Haiku was
# probed against Sonnet 5 once there is a render's worth of Terra output to
# compare it against; nothing here should be read as ruling that out.
AUTHORING_MODEL = "gpt-5.6-terra"

# Backoff for the transient failures of a many-call run (mirrors
# adapters.llm.anthropic._create_with_backoff and
# adapters.image_gen.openai_image's rate-limit backoff).
_MAX_RETRIES = 5
_RETRY_BASE_SECONDS = 2.0
_RETRY_MAX_SECONDS = 30.0


async def _create_with_backoff(client: AsyncOpenAI, **kwargs):
    """Call the chat completions API, retrying only the failures about timing."""
    delay = _RETRY_BASE_SECONDS
    for attempt in range(_MAX_RETRIES):
        try:
            return await client.chat.completions.create(**kwargs)
        except (APITimeoutError, APIConnectionError, RateLimitError, InternalServerError):
            if attempt == _MAX_RETRIES - 1:
                raise
            await asyncio.sleep(delay + random.uniform(0, 1.0))
            delay = min(delay * 2, _RETRY_MAX_SECONDS)
    raise RuntimeError("unreachable")


def _extract_json(text: str) -> str:
    """Strip markdown code fences from a response if present."""
    import re

    match = re.search(r"```(?:json)?\s*([\s\S]+?)\s*```", text)
    return match.group(1) if match else text.strip()


class OpenAILLMAdapter(LLMAdapter):
    """
    OpenAI implementation of the two authoring calls, delegating the vision
    quality check to an internal Anthropic adapter (see module docstring).
    """

    def __init__(self, model: str = AUTHORING_MODEL) -> None:
        api_key = os.environ.get("OPENAI_API_KEY")
        self._client = AsyncOpenAI(api_key=api_key)
        self._model = model
        self._anthropic = AnthropicLLMAdapter()

    async def write_script(
        self,
        topic: str,
        brief: str,
        include_hook: bool = True,
        target_minutes: float = 0.0,
    ) -> ScriptResult:
        prompt = _prompts.write_script_prompt(topic, brief, target_minutes)
        cache_key = _cache.make_key(
            {
                "role": "write_script",
                "provider": "openai",
                "prompt_version": _prompts.WRITE_SCRIPT_PROMPT_VERSION,
                "model": self._model,
                "topic": topic,
                "brief": brief,
                "include_hook": include_hook,
                "target_minutes": target_minutes,
            }
        )
        cached = _cache.load("openai_script", cache_key)
        if cached is not None:
            return ScriptResult(beats=cached["beats"], cost_usd=0.0)
        try:
            response = await _create_with_backoff(
                self._client,
                model=self._model,
                max_completion_tokens=8192,
                response_format={"type": "json_object"},
                messages=[{"role": "user", "content": prompt}],
            )
            usage = response.usage
            cost_usd = pricing.openai_chat_cost(
                self._model,
                input_tokens=usage.prompt_tokens,
                output_tokens=usage.completion_tokens,
            )
            raw = response.choices[0].message.content or ""
            data = json.loads(_extract_json(raw))
            hook = str(data.get("hook", "")).strip()
            raw_levels = data.get("levels")
            if not isinstance(raw_levels, list) or not raw_levels:
                raise ValueError("OpenAI write_script returned no levels.")
            levels: list[dict] = []
            for entry in raw_levels:
                name = str(entry.get("name", "")).strip()
                beats = [
                    str(b).strip() for b in entry.get("beats", []) if str(b).strip()
                ]
                if name and beats:
                    levels.append({"name": name, "beats": beats})
            if not levels:
                raise ValueError("OpenAI write_script returned no usable levels.")
            beats_flat = fixture_to_beats(
                {"hook": hook, "levels": levels}, include_hook=include_hook
            )
            _cache.store("openai_script", cache_key, {"beats": beats_flat})
            return ScriptResult(beats=beats_flat, cost_usd=cost_usd)
        except APIError as exc:
            raise RuntimeError(f"OpenAI write_script API error: {exc}") from exc
        except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
            raise RuntimeError(f"OpenAI write_script parse error: {exc}") from exc

    async def visualize_beats(
        self, beats: list[str], topic: str = ""
    ) -> VisualBeatsResult:
        if not beats:
            return VisualBeatsResult(descriptions=[], cost_usd=0.0)

        cache_key = _cache.make_key(
            {
                "role": "visualize_beats",
                "provider": "openai",
                "prompt_version": _prompts.VISUALIZE_BEATS_PROMPT_VERSION,
                "model": self._model,
                "beats": beats,
                "topic": topic,
            }
        )
        cached = _cache.load("openai_visual_beats", cache_key)
        if cached is not None:
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
            "openai_visual_beats",
            cache_key,
            {"descriptions": descriptions, "shot_types": shot_types},
        )
        return VisualBeatsResult(
            descriptions=descriptions, shot_types=shot_types, cost_usd=cost_usd
        )

    async def _visualize_chunk(
        self, beats: list[str], topic: str = "", lead_in: list[str] | None = None
    ) -> tuple[dict[int, tuple[str, str]], float]:
        prompt = _prompts.visualize_chunk_prompt(beats, topic, lead_in)
        try:
            response = await _create_with_backoff(
                self._client,
                model=self._model,
                max_completion_tokens=4096,
                response_format={"type": "json_object"},
                messages=[{"role": "user", "content": prompt}],
            )
            usage = response.usage
            cost_usd = pricing.openai_chat_cost(
                self._model,
                input_tokens=usage.prompt_tokens,
                output_tokens=usage.completion_tokens,
            )
            raw = response.choices[0].message.content or ""
            data = json.loads(_extract_json(raw))
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
        except APIError as exc:
            raise RuntimeError(f"OpenAI visualize_beats API error: {exc}") from exc
        except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
            raise RuntimeError(f"OpenAI visualize_beats parse error: {exc}") from exc
        return scenes, cost_usd

    async def breakdown_shots(
        self, script: list[str], character_descriptor: str
    ) -> ShotBreakdownResult:
        # Never called by the current graph (shot_breakdown.py builds shots
        # deterministically from visualize_beats output, not this method);
        # delegated rather than reimplemented so the interface stays
        # satisfied without a second copy of dead code.
        return await self._anthropic.breakdown_shots(script, character_descriptor)

    async def quality_check(
        self,
        shot_id: str,
        clip_url: str,
        still_url: str,
        style_descriptor: str,
        sheet_image_urls: list[str],
    ) -> QualityCheckResult:
        return await self._anthropic.quality_check(
            shot_id=shot_id,
            clip_url=clip_url,
            still_url=still_url,
            style_descriptor=style_descriptor,
            sheet_image_urls=sheet_image_urls,
        )
