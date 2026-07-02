"""
Tests for the still-first invariant.

A motion shot MUST have a derived still anchored to the character reference
sheet before any video-generation call.  Calling the video adapter with an
empty source_still_url is rejected at two layers:

1. graph/validation.py: assert_still_before_video raises ValueError.
2. adapters/video_gen/mock.py: MockVideoGenAdapter raises ValueError if
   source_still_url is empty (mirrors what the real adapter must enforce).
"""

from __future__ import annotations

import pytest

from adapters.video_gen.mock import MockVideoGenAdapter
from graph.nodes.generate_shots import process_shot
from graph.state import CharacterRefs, PipelineState, Shot, ShotMode, ShotStatus
from graph.validation import assert_still_before_video


class TestAssertStillBeforeVideo:
    def test_motion_shot_with_still_passes(self):
        shot = Shot(id="s1", prompt="p", mode=ShotMode.motion, still_url="file:///some/still.png")
        assert_still_before_video(shot)  # should not raise

    def test_motion_shot_without_still_raises(self):
        shot = Shot(id="s1", prompt="p", mode=ShotMode.motion, still_url="")
        with pytest.raises(ValueError, match="no derived still"):
            assert_still_before_video(shot)

    def test_static_pan_without_still_passes(self):
        shot = Shot(id="s1", prompt="p", mode=ShotMode.static_pan, still_url="")
        assert_still_before_video(shot)  # static_pan does not need a still guard


class TestMockVideoGenAdapterEnforcement:
    @pytest.mark.asyncio
    async def test_empty_still_url_rejected(self):
        adapter = MockVideoGenAdapter()
        with pytest.raises(ValueError, match="source_still_url"):
            await adapter.generate_clip(
                source_still_url="",
                prompt="some motion prompt",
                duration_seconds=5.0,
                model="mock-model",
            )

    @pytest.mark.asyncio
    async def test_non_empty_still_url_accepted(self):
        adapter = MockVideoGenAdapter()
        result = await adapter.generate_clip(
            source_still_url="file:///stills/s1.png",
            prompt="some motion prompt",
            duration_seconds=5.0,
            model="mock-model",
        )
        assert result.clip_url != ""


class TestProcessShotStillFirst:
    """
    Test that process_shot derives a still before calling the video adapter,
    and that the invariant is satisfied for motion shots end-to-end.
    """

    @pytest.mark.asyncio
    async def test_motion_shot_receives_still_and_clip(self):
        from adapters.image_gen.mock import MockImageGenAdapter
        from adapters.llm.mock import MockLLMAdapter

        shot = Shot(id="shot_000", prompt="hook shot", mode=ShotMode.motion)
        char_refs = CharacterRefs(
            sheet_image_urls=["file:///refs/front.png"],
            style_descriptor="glowing amber left eye",
        )
        state = PipelineState(shot_list=[shot], character_refs=char_refs)

        result = await process_shot(
            state,
            image_gen=MockImageGenAdapter(),
            video_gen=MockVideoGenAdapter(),
            llm=MockLLMAdapter(),
        )
        updated_shot = result["shot_list"][0]
        assert updated_shot.still_url != "", "still_url must be set for motion shot"
        assert updated_shot.clip_url != "", "clip_url must be set for motion shot"
        assert updated_shot.status == ShotStatus.approved

    @pytest.mark.asyncio
    async def test_static_pan_shot_receives_still_no_clip(self):
        from adapters.image_gen.mock import MockImageGenAdapter
        from adapters.llm.mock import MockLLMAdapter

        shot = Shot(id="shot_001", prompt="landscape pan", mode=ShotMode.static_pan)
        char_refs = CharacterRefs(
            sheet_image_urls=["file:///refs/front.png"],
            style_descriptor="glowing amber left eye",
        )
        state = PipelineState(shot_list=[shot], character_refs=char_refs)

        result = await process_shot(
            state,
            image_gen=MockImageGenAdapter(),
            video_gen=MockVideoGenAdapter(),
            llm=MockLLMAdapter(),
        )
        updated_shot = result["shot_list"][0]
        assert updated_shot.still_url != "", "still_url must be set even for static_pan"
        assert updated_shot.clip_url == "", "clip_url must be empty for static_pan"
        assert updated_shot.status == ShotStatus.approved
