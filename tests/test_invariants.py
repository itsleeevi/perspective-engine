"""
Tests for hard invariants enforced in code.

Covers:
- Real-person rejection at ideate
- Disclosure flag set at generate_metadata / publish
- Publish cadence cap
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from graph.nodes.generate_metadata import generate_metadata
from graph.nodes.ideate import ideate
from graph.nodes.publish import publish
from graph.state import CharacterRefs, Metadata, PipelineState
from graph.validation import assert_no_real_person, assert_still_before_video, set_disclosure_flag


# ── Real-person guard ─────────────────────────────────────────────────────────


class TestRealPersonGuard:
    def test_known_real_person_raises(self):
        with pytest.raises(ValueError, match="real, identifiable person"):
            assert_no_real_person("a day in the life of Elon Musk")

    def test_case_insensitive(self):
        with pytest.raises(ValueError):
            assert_no_real_person("TAYLOR SWIFT performing live")

    def test_fictional_topic_passes(self):
        assert_no_real_person("a photon's journey from the sun to your eye")

    def test_composite_topic_passes(self):
        assert_no_real_person("an unnamed deep-sea creature navigating darkness")

    @pytest.mark.asyncio
    async def test_ideate_rejects_real_person(self):
        state = PipelineState(topic="interview with Elon Musk")
        with pytest.raises(ValueError, match="real, identifiable person"):
            await ideate(state)

    @pytest.mark.asyncio
    async def test_ideate_accepts_fictional_topic(self):
        state = PipelineState(topic="a bee's morning foraging flight")
        result = await ideate(state)
        assert result["topic"] == "a bee's morning foraging flight"
        assert "brief" in result
        assert len(result["brief"]) > 0

    @pytest.mark.asyncio
    async def test_ideate_requires_non_empty_topic(self):
        state = PipelineState(topic="")
        with pytest.raises(ValueError, match="topic must be set"):
            await ideate(state)


# ── Disclosure flag ───────────────────────────────────────────────────────────


class TestDisclosureFlag:
    def test_set_disclosure_flag_mutates_dict(self):
        d = {"synthetic_content_disclosure": False, "title": "test"}
        result = set_disclosure_flag(d)
        assert result["synthetic_content_disclosure"] is True
        assert result is d  # mutated in place

    @pytest.mark.asyncio
    async def test_generate_metadata_sets_disclosure(self):
        state = PipelineState(topic="a bee's flight", brief="Short description")
        result = await generate_metadata(state)
        assert result["metadata"].synthetic_content_disclosure is True

    @pytest.mark.asyncio
    async def test_publish_rejects_missing_disclosure(self):
        state = PipelineState(
            metadata=Metadata(
                title="test",
                synthetic_content_disclosure=False,  # not set
            )
        )
        with pytest.raises(ValueError, match="synthetic_content_disclosure"):
            await publish(state)

    @pytest.mark.asyncio
    async def test_publish_accepts_disclosure_set(self):
        state = PipelineState(
            metadata=Metadata(
                title="test",
                synthetic_content_disclosure=True,
            )
        )
        result = await publish(state)
        assert "last_published_at" in result


# ── Publish cadence cap ───────────────────────────────────────────────────────


class TestPublishCadenceCap:
    @pytest.mark.asyncio
    async def test_first_publish_always_allowed(self):
        state = PipelineState(
            metadata=Metadata(synthetic_content_disclosure=True),
            last_published_at="",
        )
        result = await publish(state)
        assert result["last_published_at"] != ""

    @pytest.mark.asyncio
    async def test_second_publish_too_soon_raises(self):
        from graph.config import PUBLISH_CADENCE_SECONDS

        t0 = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        # second publish attempt only 1 second later
        t1 = datetime(2026, 1, 1, 12, 0, 1, tzinfo=timezone.utc)

        state = PipelineState(
            metadata=Metadata(synthetic_content_disclosure=True),
            last_published_at=t0.isoformat(),
        )
        with pytest.raises(ValueError, match="cadence cap"):
            await publish(state, _now=t1)

    @pytest.mark.asyncio
    async def test_second_publish_after_cadence_window_allowed(self):
        from graph.config import PUBLISH_CADENCE_SECONDS

        t0 = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        t1 = datetime(2026, 1, 2, 12, 0, 1, tzinfo=timezone.utc)  # > 24 h later

        state = PipelineState(
            metadata=Metadata(synthetic_content_disclosure=True),
            last_published_at=t0.isoformat(),
        )
        result = await publish(state, _now=t1)
        assert result["last_published_at"] != ""
