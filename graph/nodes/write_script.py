"""
write_script node — produce the ordered narration beats.

Two sources, in priority order:

1. A script fixture (``script_fixture_path``, or auto-resolved from the topic).
   Level POV scripts are long-form and heavily structured, so a reviewed fixture
   beats a generated script for both quality and cost — and makes runs
   reproducible, which the whole per-beat timing chain depends on.
2. The script LLM, for topics without a fixture.

Beats prefixed with ``[TITLE]`` are level cards, not narration.
"""

from __future__ import annotations

from adapters.llm.base import LLMAdapter
from graph.script_fixture import (
    fixture_to_beats,
    is_title_beat,
    load_fixture,
    resolve_fixture_path,
)
from graph.state import CostEntry, PipelineState


async def write_script(state: PipelineState, llm: LLMAdapter) -> dict:
    """
    Return the ordered script beats.

    Returns a partial state update: ``script``, ``script_fixture_path``,
    ``cost_log``.
    """
    fixture_path = resolve_fixture_path(state.topic, state.script_fixture_path)

    if fixture_path:
        data = load_fixture(fixture_path)
        if state.max_levels > 0:
            data = {**data, "levels": data["levels"][: state.max_levels]}
        beats = fixture_to_beats(data, include_hook=state.include_hook)
        cost = CostEntry(node="write_script", provider="fixture", amount_usd=0.0)
        update: dict = {
            "script": beats,
            "script_fixture_path": fixture_path,
            "cost_log": [cost],
        }
        # Fixtures for non-career formats (detention explainers, etc.) can
        # opt out of the rank-clothing escalation that career-ladder videos use.
        if "hero_career_progression" in data:
            update["hero_career_progression"] = bool(data["hero_career_progression"])
        return update

    result = await llm.write_script(
        topic=state.topic,
        brief=state.brief,
        include_hook=state.include_hook,
        target_minutes=state.target_minutes,
    )
    beats = result.beats
    if not beats:
        raise ValueError(
            "LLM returned an empty script; at least a hook line is required."
        )
    if all(is_title_beat(b) for b in beats):
        raise ValueError("Script contains title cards but no narration beats.")
    cost = CostEntry(node="write_script", provider="llm", amount_usd=result.cost_usd)
    return {"script": beats, "cost_log": [cost]}
