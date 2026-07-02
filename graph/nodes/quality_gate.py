"""
quality_gate — per-shot quality and identity check logic.

This module exposes:
    check_quality(shot, char_refs, llm) → QualityCheckResult
        Pure helper called by process_shot inside the retry loop.  Testable
        in isolation.

    quality_gate(state, llm) → dict
        Standalone graph node — used in unit tests for node-level behavior
        and as a reference for the quality-check contract.  NOT wired as a
        graph node in the production graph (the retry loop lives inside
        process_shot so that LangGraph's barrier count is always correct).

    quality_gate_router(state) → str
        Router function that maps shot status to the next node name.
        Used in unit tests to verify the routing logic in isolation.
"""

from __future__ import annotations

from adapters.llm.base import LLMAdapter, QualityCheckResult
from graph.config import MAX_SHOT_RETRIES
from graph.state import CharacterRefs, CostEntry, PipelineState, Shot, ShotStatus


def _coerce(state) -> PipelineState:
    if isinstance(state, PipelineState):
        return state
    return PipelineState.model_validate(state)


# ── Reusable helper ───────────────────────────────────────────────────────────


async def check_quality(
    shot: Shot,
    char_refs: CharacterRefs,
    llm: LLMAdapter,
) -> QualityCheckResult:
    """
    Call the LLM quality check for a single shot.

    Pure helper used by process_shot.  Accepts model instances directly so
    it is easily testable without building a full PipelineState.
    """
    return await llm.quality_check(
        shot_id=shot.id,
        clip_url=shot.clip_url,
        still_url=shot.still_url,
        style_descriptor=char_refs.style_descriptor,
        sheet_image_urls=char_refs.sheet_image_urls,
    )


# ── Standalone node (unit tests only) ────────────────────────────────────────


async def quality_gate(state, llm: LLMAdapter) -> dict:
    """
    Standalone quality-gate node for unit tests.

    Checks quality for the single shot in the sub-state and returns an
    updated shot with approved / failed / escalated status.  This node is
    NOT wired in the production graph; the retry loop is handled inside
    process_shot so that LangGraph barrier counts remain correct.
    """
    state = _coerce(state)
    shot: Shot = state.shot_list[0]
    char_refs = state.character_refs

    result = await check_quality(shot=shot, char_refs=char_refs, llm=llm)

    if result.passed:
        shot = shot.model_copy(update={"status": ShotStatus.approved})
    else:
        new_retry_count = shot.retry_count + 1
        if new_retry_count >= MAX_SHOT_RETRIES:
            shot = shot.model_copy(
                update={
                    "retry_count": new_retry_count,
                    "status": ShotStatus.escalated,
                    "escalated": True,
                    "quality_failure_reason": result.failure_reason,
                }
            )
        else:
            shot = shot.model_copy(
                update={
                    "retry_count": new_retry_count,
                    "status": ShotStatus.failed,
                    "quality_failure_reason": result.failure_reason,
                }
            )

    cost = CostEntry(node="quality_gate", provider="llm", amount_usd=0.0)
    return {"shot_list": [shot], "cost_log": [cost]}


# ── Router (unit tests only) ──────────────────────────────────────────────────


def quality_gate_router(state) -> str:
    """
    Route after quality_gate:
        - approved or escalated → "generate_voiceover"  (fan-in; shot done)
        - failed                → "generate_shot"        (retry this shot)

    Used in unit tests to verify routing logic in isolation.
    """
    state = _coerce(state)
    shot: Shot = state.shot_list[0]

    if shot.status in (ShotStatus.approved, ShotStatus.escalated):
        return "generate_voiceover"
    return "generate_shot"
