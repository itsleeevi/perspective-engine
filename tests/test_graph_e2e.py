"""
End-to-end test: full mocked run from ideate to publish through both gates.

LangGraph 1.2.x notes:
- ainvoke returns {"__interrupt__": [...]} when paused.
- Final result values are Pydantic model instances (use attribute access).
"""

from __future__ import annotations

import pytest
from langgraph.types import Command

from tests.conftest import APPROVAL_FINAL, APPROVAL_SCRIPT, initial_state, make_graph


def _is_interrupted(result: dict) -> bool:
    return bool(result.get("__interrupt__"))


@pytest.fixture
def e2e_graph():
    return make_graph()


class TestFullRunHappyPath:
    @pytest.mark.asyncio
    async def test_e2e_completes_with_both_approvals(self, e2e_graph):
        config = {"configurable": {"thread_id": "e2e-happy"}}
        r1 = await e2e_graph.ainvoke(initial_state(), config)
        assert _is_interrupted(r1)
        r2 = await e2e_graph.ainvoke(Command(resume=APPROVAL_SCRIPT), config)
        assert _is_interrupted(r2)
        result = await e2e_graph.ainvoke(Command(resume=APPROVAL_FINAL), config)
        assert result["last_published_at"] != ""
        assert not _is_interrupted(result)

    @pytest.mark.asyncio
    async def test_e2e_final_state_shot_list_complete(self, e2e_graph):
        """All shots must be approved or escalated after the full run."""
        from graph.state import ShotStatus

        config = {"configurable": {"thread_id": "e2e-shots"}}
        await e2e_graph.ainvoke(initial_state(), config)
        await e2e_graph.ainvoke(Command(resume=APPROVAL_SCRIPT), config)
        result = await e2e_graph.ainvoke(Command(resume=APPROVAL_FINAL), config)

        terminal = {ShotStatus.approved, ShotStatus.escalated}
        for shot in result["shot_list"]:
            status = shot.status if hasattr(shot, "status") else ShotStatus(shot["status"])
            assert status in terminal, (
                f"Shot has non-terminal status {status!r}"
            )

    @pytest.mark.asyncio
    async def test_e2e_disclosure_flag_set_in_final_state(self, e2e_graph):
        config = {"configurable": {"thread_id": "e2e-disclosure"}}
        await e2e_graph.ainvoke(initial_state(), config)
        await e2e_graph.ainvoke(Command(resume=APPROVAL_SCRIPT), config)
        result = await e2e_graph.ainvoke(Command(resume=APPROVAL_FINAL), config)
        meta = result["metadata"]
        flag = (
            meta.synthetic_content_disclosure
            if hasattr(meta, "synthetic_content_disclosure")
            else meta["synthetic_content_disclosure"]
        )
        assert flag is True

    @pytest.mark.asyncio
    async def test_e2e_voiceover_and_video_path_set(self, e2e_graph):
        config = {"configurable": {"thread_id": "e2e-assets"}}
        await e2e_graph.ainvoke(initial_state(), config)
        await e2e_graph.ainvoke(Command(resume=APPROVAL_SCRIPT), config)
        result = await e2e_graph.ainvoke(Command(resume=APPROVAL_FINAL), config)
        assert result["voiceover_url"] != ""
        assert result["final_video_path"] != ""

    @pytest.mark.asyncio
    async def test_e2e_cost_log_populated(self, e2e_graph):
        config = {"configurable": {"thread_id": "e2e-cost"}}
        await e2e_graph.ainvoke(initial_state(), config)
        await e2e_graph.ainvoke(Command(resume=APPROVAL_SCRIPT), config)
        result = await e2e_graph.ainvoke(Command(resume=APPROVAL_FINAL), config)
        assert len(result["cost_log"]) > 0

    @pytest.mark.asyncio
    async def test_e2e_character_refs_populated_after_first_approval(self, e2e_graph):
        config = {"configurable": {"thread_id": "e2e-refs"}}
        await e2e_graph.ainvoke(initial_state(), config)
        await e2e_graph.ainvoke(Command(resume=APPROVAL_SCRIPT), config)
        snap = e2e_graph.get_state(config)
        refs = snap.values.get("character_refs")
        assert refs is not None
        sheet_urls = (
            refs.sheet_image_urls if hasattr(refs, "sheet_image_urls")
            else refs.get("sheet_image_urls", [])
        )
        assert len(sheet_urls) > 0
        descriptor = (
            refs.style_descriptor if hasattr(refs, "style_descriptor")
            else refs.get("style_descriptor", "")
        )
        assert descriptor != ""


class TestRunWithRetries:
    @pytest.mark.asyncio
    async def test_e2e_with_one_retry_completes(self):
        g = make_graph(quality_fail_shot_ids=["shot_000"], fail_times=1)
        config = {"configurable": {"thread_id": "e2e-retry-pass"}}
        await g.ainvoke(initial_state(), config)
        await g.ainvoke(Command(resume=APPROVAL_SCRIPT), config)
        result = await g.ainvoke(Command(resume=APPROVAL_FINAL), config)
        assert result["last_published_at"] != ""

    @pytest.mark.asyncio
    async def test_e2e_with_cap_hit_shot_is_escalated(self):
        from graph.config import MAX_SHOT_RETRIES
        from graph.state import ShotStatus

        g = make_graph(
            quality_fail_shot_ids=["shot_000"],
            fail_times=MAX_SHOT_RETRIES + 5,
        )
        config = {"configurable": {"thread_id": "e2e-escalated"}}
        await g.ainvoke(initial_state(), config)
        await g.ainvoke(Command(resume=APPROVAL_SCRIPT), config)
        result = await g.ainvoke(Command(resume=APPROVAL_FINAL), config)

        shot_000 = next(
            (s for s in result["shot_list"]
             if (s.id if hasattr(s, "id") else s["id"]) == "shot_000"),
            None,
        )
        assert shot_000 is not None
        status = shot_000.status if hasattr(shot_000, "status") else ShotStatus(shot_000["status"])
        assert status == ShotStatus.escalated
        escalated_flag = (
            shot_000.escalated if hasattr(shot_000, "escalated")
            else shot_000["escalated"]
        )
        assert escalated_flag is True


class TestEditPayloadAtGates:
    @pytest.mark.asyncio
    async def test_script_edit_applied_and_logged(self, e2e_graph):
        config = {"configurable": {"thread_id": "e2e-edit-script"}}
        await e2e_graph.ainvoke(initial_state(), config)

        edited_script = ["[HOOK] Edited hook line.", "Beat 2", "Beat 3"]
        resume_payload = {
            "approved": True,
            "edits": [{"field_path": "script", "new_value": edited_script, "note": "tighter hook"}],
        }
        await e2e_graph.ainvoke(Command(resume=resume_payload), config)

        snap = e2e_graph.get_state(config)
        assert snap.values["script"] == edited_script
        edits = snap.values.get("human_edits_log", [])
        paths = [
            (e.field_path if hasattr(e, "field_path") else e["field_path"])
            for e in edits
        ]
        assert "script" in paths

    @pytest.mark.asyncio
    async def test_metadata_edit_applied_at_final_gate(self, e2e_graph):
        config = {"configurable": {"thread_id": "e2e-edit-meta"}}
        await e2e_graph.ainvoke(initial_state(), config)
        await e2e_graph.ainvoke(Command(resume=APPROVAL_SCRIPT), config)

        resume_payload = {
            "approved": True,
            "edits": [{"field_path": "metadata.title", "new_value": "Custom Title", "note": "better"}],
        }
        result = await e2e_graph.ainvoke(Command(resume=resume_payload), config)
        meta = result["metadata"]
        title = meta.title if hasattr(meta, "title") else meta["title"]
        assert title == "Custom Title"
        edits = result.get("human_edits_log", [])
        paths = [
            (e.field_path if hasattr(e, "field_path") else e["field_path"])
            for e in edits
        ]
        assert "metadata.title" in paths
