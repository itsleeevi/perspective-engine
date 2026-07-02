"""
generate_shots node — fan-out: one per-shot worker dispatched per shot.

Control-flow:
    ``dispatch_shots`` (conditional edge after generate_character_refs) returns
    one ``Send("process_shot", per_shot_state)`` per shot.  Each ``process_shot``
    sub-execution handles the complete per-shot lifecycle:
        derive still → generate clip (motion only) → quality check → retry if
        needed (up to MAX_SHOT_RETRIES) → mark approved or escalated.
    After every ``process_shot`` completes, a fixed edge routes to
    ``generate_voiceover``.  LangGraph applies barrier semantics: the voiceover
    node runs exactly once after ALL per-shot sub-executions reach it.

Design note:
    The retry loop lives inside ``process_shot`` (not as graph edges) so that
    the barrier count is always equal to the number of shots dispatched.  If the
    retry were a conditional graph edge (quality_gate → generate_shot) the first
    completion would fire the barrier before remaining shots finish.

Invariants enforced here:
    - Every motion shot must have a derived still before the video adapter is
      called (assert_still_before_video).
    - static_pan shots receive a still but no video-gen call.
    - Per-shot retry count is capped at MAX_SHOT_RETRIES then escalated.
"""

from __future__ import annotations

from langgraph.types import Send

from adapters.image_gen.base import ImageGenAdapter
from adapters.llm.base import LLMAdapter
from adapters.video_gen.base import VideoGenAdapter
from graph.config import MAX_SHOT_RETRIES
from graph.nodes.quality_gate import check_quality
from graph.state import CostEntry, PipelineState, Shot, ShotMode, ShotStatus
from graph.validation import assert_still_before_video


def _coerce(state) -> PipelineState:
    """
    Coerce the incoming state to PipelineState.

    Nodes dispatched via Send receive a plain dict from the checkpointer
    (msgpack deserialization does not restore Pydantic model types).
    """
    if isinstance(state, PipelineState):
        return state
    return PipelineState.model_validate(state)


# ── Edge function (conditional edge after generate_character_refs) ────────────


def dispatch_shots(state: PipelineState) -> list[Send]:
    """
    Return one Send per shot in the shot list.

    Each Send starts a process_shot sub-execution with a per-shot slice of
    state.  After process_shot completes, a fixed edge routes to
    generate_voiceover so the barrier count equals the number of shots.
    """
    return [
        Send(
            "process_shot",
            {
                "shot_list": [shot],
                "character_refs": state.character_refs,
            },
        )
        for shot in state.shot_list
    ]


# ── Per-shot worker (dispatched via Send) ─────────────────────────────────────


async def process_shot(
    state,
    image_gen: ImageGenAdapter,
    video_gen: VideoGenAdapter,
    llm: LLMAdapter,
) -> dict:
    """
    Full per-shot lifecycle: derive still → generate clip → quality check loop.

    Receives a per-shot sub-state (shot_list contains exactly one shot).
    Returns a partial state update with the final shot status and cost entries.

    Retry loop: on quality-check failure, re-derives the still and re-generates
    the clip.  After MAX_SHOT_RETRIES consecutive failures the shot is
    escalated (human review required) and the loop exits.
    """
    state = _coerce(state)
    shot: Shot = state.shot_list[0]
    char_refs = state.character_refs
    cost_entries: list[CostEntry] = []

    for _attempt in range(MAX_SHOT_RETRIES + 1):
        # 1. Derive a per-shot still anchored to the reference sheet.
        still_result = await image_gen.derive_still(
            shot_prompt=shot.prompt,
            sheet_image_urls=char_refs.sheet_image_urls,
            style_descriptor=char_refs.style_descriptor,
        )
        shot = shot.model_copy(update={"still_url": still_result.still_url})
        cost_entries.append(
            CostEntry(node="process_shot:still", provider="image_gen", amount_usd=0.0)
        )

        # 2. For motion shots: enforce still-first, then animate.
        if shot.mode == ShotMode.motion:
            assert_still_before_video(shot)
            clip_result = await video_gen.generate_clip(
                source_still_url=shot.still_url,
                prompt=shot.prompt,
                duration_seconds=shot.duration_seconds,
                model=shot.assigned_model,
            )
            shot = shot.model_copy(update={"clip_url": clip_result.clip_url})
            cost_entries.append(
                CostEntry(node="process_shot:clip", provider="video_gen", amount_usd=0.0)
            )

        # 3. Quality check.
        qc_result = await check_quality(
            shot=shot,
            char_refs=char_refs,
            llm=llm,
        )
        cost_entries.append(
            CostEntry(node="process_shot:quality", provider="llm", amount_usd=0.0)
        )

        if qc_result.passed:
            shot = shot.model_copy(update={"status": ShotStatus.approved})
            break

        new_retry_count = shot.retry_count + 1
        if new_retry_count >= MAX_SHOT_RETRIES:
            shot = shot.model_copy(
                update={
                    "retry_count": new_retry_count,
                    "status": ShotStatus.escalated,
                    "escalated": True,
                    "quality_failure_reason": qc_result.failure_reason,
                }
            )
            break

        shot = shot.model_copy(
            update={
                "retry_count": new_retry_count,
                "status": ShotStatus.failed,
                "quality_failure_reason": qc_result.failure_reason,
            }
        )
        # Continue to next attempt.

    return {"shot_list": [shot], "cost_log": cost_entries}
