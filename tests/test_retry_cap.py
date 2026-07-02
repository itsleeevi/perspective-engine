"""
Tests for the quality-gate retry-cap invariant.

Repeated quality-gate failures must escalate rather than loop forever.
Once a shot's retry_count reaches MAX_SHOT_RETRIES it is marked
``escalated``.  The quality_gate node itself enforces this; these tests
verify the node in isolation.
"""

from __future__ import annotations

import pytest

from adapters.llm.mock import MockLLMAdapter
from graph.config import MAX_SHOT_RETRIES
from graph.nodes.quality_gate import quality_gate, quality_gate_router
from graph.state import CharacterRefs, PipelineState, Shot, ShotMode, ShotStatus


def _state_with_shot(shot: Shot) -> PipelineState:
    return PipelineState(
        shot_list=[shot],
        character_refs=CharacterRefs(
            sheet_image_urls=["file:///refs/front.png"],
            style_descriptor="distinctive amber eye",
        ),
    )


class TestQualityGateRetryCap:
    @pytest.mark.asyncio
    async def test_passing_shot_is_approved(self):
        shot = Shot(id="s1", prompt="p", status=ShotStatus.quality_check)
        state = _state_with_shot(shot)
        llm = MockLLMAdapter()  # no failures configured
        result = await quality_gate(state, llm=llm)
        assert result["shot_list"][0].status == ShotStatus.approved

    @pytest.mark.asyncio
    async def test_first_failure_increments_retry_count(self):
        shot = Shot(id="s1", prompt="p", status=ShotStatus.quality_check)
        state = _state_with_shot(shot)
        llm = MockLLMAdapter(quality_fail_shot_ids=["s1"], fail_times=1)
        result = await quality_gate(state, llm=llm)
        updated = result["shot_list"][0]
        assert updated.status == ShotStatus.failed
        assert updated.retry_count == 1
        assert updated.escalated is False

    @pytest.mark.asyncio
    async def test_cap_reached_escalates_shot(self):
        """After MAX_SHOT_RETRIES failures the shot is escalated, not retried."""
        shot = Shot(
            id="s1",
            prompt="p",
            status=ShotStatus.quality_check,
            retry_count=MAX_SHOT_RETRIES - 1,  # one more failure will hit the cap
        )
        state = _state_with_shot(shot)
        # fail_times > remaining retries → will always fail
        llm = MockLLMAdapter(quality_fail_shot_ids=["s1"], fail_times=999)
        result = await quality_gate(state, llm=llm)
        updated = result["shot_list"][0]
        assert updated.status == ShotStatus.escalated
        assert updated.escalated is True
        assert updated.retry_count == MAX_SHOT_RETRIES

    @pytest.mark.asyncio
    async def test_quality_failure_records_reason(self):
        shot = Shot(id="s1", prompt="p", status=ShotStatus.quality_check)
        state = _state_with_shot(shot)
        llm = MockLLMAdapter(quality_fail_shot_ids=["s1"], fail_times=1)
        result = await quality_gate(state, llm=llm)
        updated = result["shot_list"][0]
        assert updated.quality_failure_reason != ""


class TestQualityGateRouter:
    def test_approved_routes_to_voiceover(self):
        shot = Shot(id="s1", prompt="p", status=ShotStatus.approved)
        state = _state_with_shot(shot)
        assert quality_gate_router(state) == "generate_voiceover"

    def test_escalated_routes_to_voiceover(self):
        shot = Shot(id="s1", prompt="p", status=ShotStatus.escalated, escalated=True)
        state = _state_with_shot(shot)
        assert quality_gate_router(state) == "generate_voiceover"

    def test_failed_routes_to_generate_shot(self):
        shot = Shot(id="s1", prompt="p", status=ShotStatus.failed, retry_count=1)
        state = _state_with_shot(shot)
        assert quality_gate_router(state) == "generate_shot"

    def test_cap_enforced_before_router(self):
        """
        The router never routes a shot with retry_count >= MAX to generate_shot.
        quality_gate itself escalates at the cap; the router just reads the status.
        """
        shot = Shot(
            id="s1",
            prompt="p",
            status=ShotStatus.escalated,  # set by quality_gate when cap is hit
            retry_count=MAX_SHOT_RETRIES,
        )
        state = _state_with_shot(shot)
        # escalated → goes to generate_voiceover, NOT generate_shot
        assert quality_gate_router(state) == "generate_voiceover"


class TestNoInfiniteLoop:
    """
    Verify that a shot with repeated failures is always escalated,
    never loops indefinitely.
    """

    @pytest.mark.asyncio
    async def test_simulate_full_retry_cycle(self):
        """
        Simulate the quality_gate node being called for every retry.
        After MAX_SHOT_RETRIES consecutive failures the shot must be escalated.
        """
        shot = Shot(id="s1", prompt="p", status=ShotStatus.quality_check)
        state = _state_with_shot(shot)
        llm = MockLLMAdapter(quality_fail_shot_ids=["s1"], fail_times=9999)

        routed_to_voiceover = False
        current_shot = shot

        for _ in range(MAX_SHOT_RETRIES + 2):  # +2 to confirm we don't loop past
            state = _state_with_shot(current_shot.model_copy(update={"status": ShotStatus.quality_check}))
            result = await quality_gate(state, llm=llm)
            current_shot = result["shot_list"][0]

            route = quality_gate_router(_state_with_shot(current_shot))
            if route == "generate_voiceover":
                routed_to_voiceover = True
                break

        assert routed_to_voiceover, "shot must be routed to voiceover (escalated) after cap"
        assert current_shot.status == ShotStatus.escalated
        assert current_shot.retry_count == MAX_SHOT_RETRIES
