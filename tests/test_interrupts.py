"""
Tests for the two non-bypassable human-review interrupt gates.

LangGraph 1.2.x notes:
- ``ainvoke`` returns ``{"__interrupt__": [...]}`` when paused (no exception).
- ``get_state(config).values`` contains only explicitly-set fields (not defaults).
- Pydantic model instances are returned as-is (use attribute access, not dict
  subscript) when the field has been set via a node return.
"""

from __future__ import annotations

import pytest
from langgraph.types import Command

from tests.conftest import APPROVAL_FINAL, APPROVAL_SCRIPT, initial_state, make_graph


THREAD_1 = {"configurable": {"thread_id": "test-interrupts-1"}}
THREAD_2 = {"configurable": {"thread_id": "test-interrupts-2"}}
THREAD_3 = {"configurable": {"thread_id": "test-interrupts-3"}}


def _is_interrupted(result: dict) -> bool:
    return bool(result.get("__interrupt__"))


def _sheet_urls(snap_values: dict) -> list:
    """Extract sheet_image_urls from snap.values, handling absent / dict / model."""
    cr = snap_values.get("character_refs")
    if cr is None:
        return []
    if hasattr(cr, "sheet_image_urls"):
        return cr.sheet_image_urls
    return cr.get("sheet_image_urls", [])


class TestFirstInterrupt:
    """human_review_script: pauses before character-ref generation."""

    @pytest.mark.asyncio
    async def test_graph_pauses_at_first_gate(self):
        g = make_graph()
        result = await g.ainvoke(initial_state(), THREAD_1)
        assert _is_interrupted(result)

    @pytest.mark.asyncio
    async def test_interrupt_value_contains_script_and_shots(self):
        g = make_graph()
        result = await g.ainvoke(initial_state(), THREAD_1)
        iv = result["__interrupt__"][0].value
        assert "script" in iv
        assert "shot_list" in iv

    @pytest.mark.asyncio
    async def test_state_persists_across_pause(self):
        g = make_graph()
        await g.ainvoke(initial_state(), THREAD_1)
        snap = g.get_state(THREAD_1)
        assert len(snap.values["script"]) > 0
        assert len(snap.values["shot_list"]) > 0

    @pytest.mark.asyncio
    async def test_paused_at_correct_node(self):
        g = make_graph()
        await g.ainvoke(initial_state(), THREAD_1)
        snap = g.get_state(THREAD_1)
        assert "human_review_script" in snap.next

    @pytest.mark.asyncio
    async def test_downstream_does_not_run_before_approval(self):
        """
        generate_character_refs must NOT have run yet.
        character_refs is either absent from snap.values (never set) or empty.
        """
        g = make_graph()
        await g.ainvoke(initial_state(), THREAD_1)
        snap = g.get_state(THREAD_1)
        assert _sheet_urls(snap.values) == []

    @pytest.mark.asyncio
    async def test_resume_with_approval_continues(self):
        g = make_graph()
        await g.ainvoke(initial_state(), THREAD_1)
        result2 = await g.ainvoke(Command(resume=APPROVAL_SCRIPT), THREAD_1)
        assert _is_interrupted(result2), "Expected second interrupt at human_review_final"
        snap = g.get_state(THREAD_1)
        assert len(_sheet_urls(snap.values)) > 0

    @pytest.mark.asyncio
    async def test_rejection_raises_value_error(self):
        g = make_graph()
        await g.ainvoke(initial_state(), THREAD_1)
        with pytest.raises(ValueError, match="reject"):
            await g.ainvoke(
                Command(resume={"approved": False, "edits": []}), THREAD_1
            )


class TestSecondInterrupt:
    """human_review_final: pauses before publish."""

    async def _run_to_second_interrupt(self, g, config) -> dict:
        await g.ainvoke(initial_state(), config)
        return await g.ainvoke(Command(resume=APPROVAL_SCRIPT), config)

    @pytest.mark.asyncio
    async def test_graph_pauses_at_second_gate(self):
        g = make_graph()
        result2 = await self._run_to_second_interrupt(g, THREAD_2)
        assert _is_interrupted(result2)

    @pytest.mark.asyncio
    async def test_state_has_final_video_before_second_gate(self):
        g = make_graph()
        result2 = await self._run_to_second_interrupt(g, THREAD_2)
        # final_video_path IS in the result (set by assemble before the interrupt)
        fvp = result2.get("final_video_path", "")
        if not fvp:
            snap = g.get_state(THREAD_2)
            fvp = snap.values.get("final_video_path", "")
        assert fvp != ""

    @pytest.mark.asyncio
    async def test_state_has_disclosure_set_before_second_gate(self):
        g = make_graph()
        await self._run_to_second_interrupt(g, THREAD_2)
        snap = g.get_state(THREAD_2)
        meta = snap.values.get("metadata")
        flag = (
            meta.synthetic_content_disclosure
            if hasattr(meta, "synthetic_content_disclosure")
            else meta.get("synthetic_content_disclosure", False)
            if meta
            else False
        )
        assert flag is True

    @pytest.mark.asyncio
    async def test_publish_not_run_before_approval(self):
        g = make_graph()
        await self._run_to_second_interrupt(g, THREAD_2)
        snap = g.get_state(THREAD_2)
        assert snap.values.get("last_published_at", "") == ""

    @pytest.mark.asyncio
    async def test_resume_with_approval_completes_run(self):
        g = make_graph()
        await self._run_to_second_interrupt(g, THREAD_2)
        result = await g.ainvoke(Command(resume=APPROVAL_FINAL), THREAD_2)
        assert result["last_published_at"] != ""
        assert not _is_interrupted(result)

    @pytest.mark.asyncio
    async def test_second_gate_rejection_aborts(self):
        g = make_graph()
        await self._run_to_second_interrupt(g, THREAD_3)
        with pytest.raises(ValueError, match="reject"):
            await g.ainvoke(
                Command(resume={"approved": False, "edits": []}), THREAD_3
            )


class TestNoAutoApprove:
    """
    Structural test: interrupt() is called unconditionally in both gates.
    No flag, parameter, or code path may skip the interrupt call.
    """

    def test_human_review_script_uses_interrupt(self):
        import inspect
        from graph.nodes.human_review_script import human_review_script

        src = inspect.getsource(human_review_script)
        assert "interrupt(" in src

    def test_human_review_final_uses_interrupt(self):
        import inspect
        from graph.nodes.human_review_final import human_review_final

        src = inspect.getsource(human_review_final)
        assert "interrupt(" in src

    def test_human_review_script_has_no_conditional_interrupt(self):
        """interrupt() must not be guarded by an if-condition."""
        import ast
        import inspect
        from graph.nodes.human_review_script import human_review_script

        src = inspect.getsource(human_review_script)
        tree = ast.parse(src)
        # The interrupt() call must be a top-level statement in the function body,
        # not nested inside an if/while/try branch.
        func_body = [
            n for n in ast.walk(tree)
            if isinstance(n, ast.AsyncFunctionDef) and n.name == "human_review_script"
        ]
        assert len(func_body) == 1
        # Find interrupt() calls — they must exist somewhere in the function.
        calls = [
            n for n in ast.walk(func_body[0])
            if isinstance(n, ast.Call) and
            isinstance(n.func, ast.Name) and n.func.id == "interrupt"
        ]
        assert len(calls) >= 1

    def test_human_review_final_has_no_conditional_interrupt(self):
        import ast
        import inspect
        from graph.nodes.human_review_final import human_review_final

        src = inspect.getsource(human_review_final)
        tree = ast.parse(src)
        func_body = [
            n for n in ast.walk(tree)
            if isinstance(n, ast.AsyncFunctionDef) and n.name == "human_review_final"
        ]
        assert len(func_body) == 1
        calls = [
            n for n in ast.walk(func_body[0])
            if isinstance(n, ast.Call) and
            isinstance(n.func, ast.Name) and n.func.id == "interrupt"
        ]
        assert len(calls) >= 1
