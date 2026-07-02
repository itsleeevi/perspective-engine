"""
Tests for fan-out correctness.

Requirements (from AGENTS.md):
- One output per shot, order-independent.
- The _merge_shots reducer correctly fans multiple per-shot updates back
  into the main shot_list.
- dispatch_shots produces exactly one Send per shot.
"""

from __future__ import annotations

import pytest
from langgraph.types import Send

from graph.nodes.generate_shots import dispatch_shots, process_shot
from graph.state import CharacterRefs, PipelineState, Shot, ShotMode, _merge_shots


def _make_shots(n: int) -> list[Shot]:
    return [Shot(id=f"shot_{i:03d}", prompt=f"beat {i}") for i in range(n)]


class TestDispatchShots:
    def test_returns_one_send_per_shot(self):
        shots = _make_shots(5)
        state = PipelineState(
            shot_list=shots,
            character_refs=CharacterRefs(
                sheet_image_urls=["file:///ref.png"],
                style_descriptor="amber eye",
            ),
        )
        sends = dispatch_shots(state)
        assert len(sends) == 5

    def test_each_send_targets_process_shot(self):
        shots = _make_shots(3)
        state = PipelineState(
            shot_list=shots,
            character_refs=CharacterRefs(),
        )
        sends = dispatch_shots(state)
        assert all(isinstance(s, Send) for s in sends)
        assert all(s.node == "process_shot" for s in sends)

    def test_each_send_carries_exactly_one_shot(self):
        shots = _make_shots(4)
        state = PipelineState(
            shot_list=shots,
            character_refs=CharacterRefs(),
        )
        sends = dispatch_shots(state)
        for send in sends:
            assert len(send.arg["shot_list"]) == 1

    def test_send_shot_ids_cover_all_shots(self):
        shots = _make_shots(4)
        state = PipelineState(
            shot_list=shots,
            character_refs=CharacterRefs(),
        )
        sends = dispatch_shots(state)
        dispatched_ids = {send.arg["shot_list"][0].id for send in sends}
        expected_ids = {s.id for s in shots}
        assert dispatched_ids == expected_ids

    def test_character_refs_included_in_each_send(self):
        shots = _make_shots(2)
        char_refs = CharacterRefs(
            sheet_image_urls=["file:///ref.png"],
            style_descriptor="amber eye",
        )
        state = PipelineState(shot_list=shots, character_refs=char_refs)
        sends = dispatch_shots(state)
        for send in sends:
            assert send.arg["character_refs"].style_descriptor == "amber eye"

    def test_empty_shot_list_produces_no_sends(self):
        state = PipelineState(shot_list=[], character_refs=CharacterRefs())
        sends = dispatch_shots(state)
        assert sends == []


class TestMergeShotsReducer:
    """
    The _merge_shots reducer is the fan-in mechanism.  These tests verify
    that parallel per-shot updates are correctly merged regardless of order.
    """

    def test_order_independent_merge(self):
        """
        Updates arriving in a different order than the original list
        should produce the same final shot_list order.
        """
        shots = _make_shots(4)
        from graph.state import ShotStatus

        # Simulate updates arriving out of order (shot 2, then shot 0)
        updates_a = [shots[2].model_copy(update={"status": ShotStatus.approved})]
        updates_b = [shots[0].model_copy(update={"status": ShotStatus.approved})]

        after_a = _merge_shots(shots, updates_a)
        after_ab = _merge_shots(after_a, updates_b)

        assert len(after_ab) == 4
        assert after_ab[0].status == ShotStatus.approved
        assert after_ab[2].status == ShotStatus.approved
        # Non-updated shots unchanged
        assert after_ab[1].status == ShotStatus.pending
        assert after_ab[3].status == ShotStatus.pending

    def test_parallel_updates_all_applied(self):
        from graph.state import ShotStatus

        shots = _make_shots(5)
        updates = [s.model_copy(update={"status": ShotStatus.approved}) for s in shots]

        # Apply all updates at once (simulating fan-in)
        result = _merge_shots(shots, updates)
        assert all(s.status == ShotStatus.approved for s in result)
        assert len(result) == 5

    def test_idempotent_update(self):
        """Applying the same update twice is safe."""
        from graph.state import ShotStatus

        shots = _make_shots(2)
        update = [shots[0].model_copy(update={"status": ShotStatus.approved})]
        after_first = _merge_shots(shots, update)
        after_second = _merge_shots(after_first, update)
        assert after_second[0].status == ShotStatus.approved
        assert len(after_second) == 2
