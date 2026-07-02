"""
Tests for state schema defaults and validation.

These tests do not run the graph; they verify that PipelineState and its
nested models enforce the correct invariants by construction.
"""

from __future__ import annotations

import pytest

from graph.state import (
    CharacterRefs,
    CostEntry,
    HumanEdit,
    Metadata,
    PipelineState,
    Shot,
    ShotMode,
    ShotStatus,
    _merge_shots,
)


class TestShotDefaults:
    def test_mode_defaults_to_static_pan(self):
        shot = Shot(id="s1", prompt="test")
        assert shot.mode == ShotMode.static_pan

    def test_status_defaults_to_pending(self):
        shot = Shot(id="s1", prompt="test")
        assert shot.status == ShotStatus.pending

    def test_retry_count_defaults_to_zero(self):
        shot = Shot(id="s1", prompt="test")
        assert shot.retry_count == 0

    def test_escalated_defaults_to_false(self):
        shot = Shot(id="s1", prompt="test")
        assert shot.escalated is False

    def test_still_and_clip_urls_default_empty(self):
        shot = Shot(id="s1", prompt="test")
        assert shot.still_url == ""
        assert shot.clip_url == ""


class TestMetadataDefaults:
    def test_disclosure_flag_defaults_false(self):
        meta = Metadata()
        assert meta.synthetic_content_disclosure is False

    def test_tags_default_empty(self):
        meta = Metadata()
        assert meta.tags == []


class TestPipelineStateDefaults:
    def test_shot_list_defaults_empty(self):
        state = PipelineState()
        assert state.shot_list == []

    def test_script_defaults_empty(self):
        state = PipelineState()
        assert state.script == []

    def test_cost_log_defaults_empty(self):
        state = PipelineState()
        assert state.cost_log == []

    def test_human_edits_log_defaults_empty(self):
        state = PipelineState()
        assert state.human_edits_log == []

    def test_character_refs_defaults_empty(self):
        state = PipelineState()
        assert state.character_refs.sheet_image_urls == []
        assert state.character_refs.style_descriptor == ""

    def test_last_published_at_defaults_empty(self):
        state = PipelineState()
        assert state.last_published_at == ""


class TestMergeShots:
    """Unit tests for the _merge_shots reducer used in fan-out."""

    def test_update_existing_shot(self):
        s1 = Shot(id="s1", prompt="original", status=ShotStatus.pending)
        s1_updated = Shot(id="s1", prompt="original", status=ShotStatus.approved)
        result = _merge_shots([s1], [s1_updated])
        assert len(result) == 1
        assert result[0].status == ShotStatus.approved

    def test_append_new_shot(self):
        s1 = Shot(id="s1", prompt="first")
        s2 = Shot(id="s2", prompt="second")
        result = _merge_shots([s1], [s2])
        assert len(result) == 2
        assert result[0].id == "s1"
        assert result[1].id == "s2"

    def test_preserves_original_order(self):
        shots = [Shot(id=f"s{i}", prompt=f"p{i}") for i in range(4)]
        updates = [
            Shot(id="s2", prompt="p2", status=ShotStatus.approved),
            Shot(id="s0", prompt="p0", status=ShotStatus.approved),
        ]
        result = _merge_shots(shots, updates)
        assert [s.id for s in result] == ["s0", "s1", "s2", "s3"]
        assert result[0].status == ShotStatus.approved
        assert result[2].status == ShotStatus.approved
        assert result[1].status == ShotStatus.pending

    def test_empty_update_preserves_state(self):
        shots = [Shot(id="s1", prompt="p")]
        result = _merge_shots(shots, [])
        assert result == shots

    def test_empty_existing_with_update(self):
        s = Shot(id="s1", prompt="p")
        result = _merge_shots([], [s])
        assert len(result) == 1
        assert result[0].id == "s1"
