"""
Tests for the human_review_images interrupt gate.

The gate fires after every process_shot sub-execution completes and before
generate_voiceover. Resume with an empty regenerate list proceeds; a non-empty
list regenerates those stills and re-interrupts; rejection aborts.
"""

from __future__ import annotations

import pytest
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command

from adapters.image_gen.mock import MockImageGenAdapter
from adapters.llm.mock import MockLLMAdapter
from adapters.video_gen.mock import MockVideoGenAdapter
from adapters.voice.mock import MockVoiceAdapter
from graph.graph import build_graph
from tests.conftest import APPROVAL_IMAGES, APPROVAL_SCRIPT, initial_state


class CountingImageGen(MockImageGenAdapter):
    def __init__(self) -> None:
        super().__init__()
        self.derive_calls: list[dict] = []

    async def derive_still(
        self,
        shot_prompt: str,
        sheet_image_urls: list[str],
        style_descriptor: str,
        attempt: int = 0,
    ):
        self.derive_calls.append(
            {"shot_prompt": shot_prompt, "attempt": attempt}
        )
        return await super().derive_still(
            shot_prompt, sheet_image_urls, style_descriptor, attempt
        )


def _make_graph(image_gen: CountingImageGen | None = None):
    gen = image_gen or CountingImageGen()
    return build_graph(
        llm=MockLLMAdapter(),
        image_gen=gen,
        video_gen=MockVideoGenAdapter(),
        voice=MockVoiceAdapter(),
        checkpointer=MemorySaver(),
    ), gen


def _is_interrupted(result: dict) -> bool:
    return bool(result.get("__interrupt__"))


def _iv(result: dict) -> dict:
    return result["__interrupt__"][0].value


def _first_still_shot(iv: dict) -> dict:
    return next(s for s in iv["shot_list"] if not s.get("is_title_card"))


def _first_title_shot(iv: dict) -> dict:
    return next(s for s in iv["shot_list"] if s.get("is_title_card"))


async def _run_to_images_gate(g, config) -> dict:
    await g.ainvoke(initial_state(), config)
    result = await g.ainvoke(Command(resume=APPROVAL_SCRIPT), config)
    assert _is_interrupted(result)
    return result


class TestImagesGateFires:
    @pytest.mark.asyncio
    async def test_interrupt_fires_after_all_stills(self):
        g, _ = _make_graph()
        config = {"configurable": {"thread_id": "img-fires"}}
        result = await _run_to_images_gate(g, config)
        iv = _iv(result)
        assert iv["gate"] == "human_review_images"
        stills = [s for s in iv["shot_list"] if not s.get("is_title_card")]
        assert stills
        assert all(s.get("still_url") for s in stills)

    @pytest.mark.asyncio
    async def test_voiceover_does_not_run_before_approval(self):
        g, _ = _make_graph()
        config = {"configurable": {"thread_id": "img-no-vo"}}
        await _run_to_images_gate(g, config)
        snap = g.get_state(config)
        assert snap.values.get("voiceover_url", "") == ""
        assert "human_review_images" in snap.next


class TestApproveAll:
    @pytest.mark.asyncio
    async def test_empty_regen_list_proceeds_without_redraw(self):
        g, image_gen = _make_graph()
        config = {"configurable": {"thread_id": "img-approve"}}
        result = await _run_to_images_gate(g, config)
        iv = _iv(result)
        stills_before = {s["id"]: s["still_url"] for s in iv["shot_list"]}
        calls_before = len(image_gen.derive_calls)

        result2 = await g.ainvoke(Command(resume=APPROVAL_IMAGES), config)
        assert _is_interrupted(result2)
        assert _iv(result2)["gate"] == "human_review_final"
        assert len(image_gen.derive_calls) == calls_before

        snap = g.get_state(config)
        for shot in snap.values["shot_list"]:
            assert shot.still_url == stills_before[shot.id]


class TestRegenerateLoop:
    @pytest.mark.asyncio
    async def test_regenerate_one_shot_redraws_and_reinterrupts(self):
        g, image_gen = _make_graph()
        config = {"configurable": {"thread_id": "img-regen"}}
        result = await _run_to_images_gate(g, config)
        iv = _iv(result)
        target = _first_still_shot(iv)
        original_url = target["still_url"]
        others = {
            s["id"]: s["still_url"]
            for s in iv["shot_list"]
            if s["id"] != target["id"]
        }
        calls_before = len(image_gen.derive_calls)

        result2 = await g.ainvoke(
            Command(
                resume={
                    "approved": True,
                    "regenerate_shot_ids": [target["id"]],
                }
            ),
            config,
        )
        assert _is_interrupted(result2)
        iv2 = _iv(result2)
        assert iv2["gate"] == "human_review_images"

        updated = next(s for s in iv2["shot_list"] if s["id"] == target["id"])
        assert updated["still_url"] != original_url
        assert updated["manual_regen_count"] == 1
        assert len(image_gen.derive_calls) == calls_before + 1
        assert image_gen.derive_calls[-1]["shot_prompt"] == target["prompt"]

        for shot in iv2["shot_list"]:
            if shot["id"] != target["id"]:
                assert shot["still_url"] == others[shot["id"]]

        result3 = await g.ainvoke(Command(resume=APPROVAL_IMAGES), config)
        assert _is_interrupted(result3)
        assert _iv(result3)["gate"] == "human_review_final"

        snap = g.get_state(config)
        edits = snap.values.get("human_edits_log", [])
        paths = [
            (e.field_path if hasattr(e, "field_path") else e["field_path"])
            for e in edits
        ]
        assert f"shot_list[{target['id']}].still_url" in paths
        notes = [
            (e.note if hasattr(e, "note") else e["note"]) for e in edits
        ]
        assert "manual regeneration" in notes


class TestReject:
    @pytest.mark.asyncio
    async def test_rejection_raises_and_skips_voiceover(self):
        g, _ = _make_graph()
        config = {"configurable": {"thread_id": "img-reject"}}
        await _run_to_images_gate(g, config)
        with pytest.raises(ValueError, match="reject"):
            await g.ainvoke(
                Command(resume={"approved": False, "regenerate_shot_ids": []}),
                config,
            )
        snap = g.get_state(config)
        assert snap.values.get("voiceover_url", "") == ""


class TestTitleCardExclusion:
    @pytest.mark.asyncio
    async def test_title_card_regen_is_noop(self):
        g, image_gen = _make_graph()
        config = {"configurable": {"thread_id": "img-title"}}
        result = await _run_to_images_gate(g, config)
        iv = _iv(result)
        title = _first_title_shot(iv)
        original_url = title["still_url"]
        calls_before = len(image_gen.derive_calls)

        result2 = await g.ainvoke(
            Command(
                resume={
                    "approved": True,
                    "regenerate_shot_ids": [title["id"]],
                }
            ),
            config,
        )
        assert _is_interrupted(result2)
        iv2 = _iv(result2)
        updated = next(s for s in iv2["shot_list"] if s["id"] == title["id"])
        assert updated["still_url"] == original_url
        assert updated.get("manual_regen_count", 0) == 0
        assert len(image_gen.derive_calls) == calls_before


class TestUsesInterrupt:
    def test_human_review_images_uses_interrupt(self):
        import inspect
        from graph.nodes.human_review_images import human_review_images

        src = inspect.getsource(human_review_images)
        assert "interrupt(" in src
