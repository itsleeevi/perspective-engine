"""
Shared fixtures for control-flow tests.

All tests use the in-memory checkpointer and deterministic mock adapters
so no external services or filesystem writes are required.
"""

from __future__ import annotations

import pytest
from langgraph.checkpoint.memory import MemorySaver

from adapters.image_gen.mock import MockImageGenAdapter
from adapters.llm.mock import MockLLMAdapter
from adapters.video_gen.mock import MockVideoGenAdapter
from adapters.voice.mock import MockVoiceAdapter
from graph.graph import build_graph


@pytest.fixture
def memory_checkpointer() -> MemorySaver:
    """A fresh in-memory checkpointer for each test."""
    return MemorySaver()


@pytest.fixture
def mock_adapters():
    """Bundle of mock adapters with no forced failures."""
    return {
        "llm": MockLLMAdapter(),
        "image_gen": MockImageGenAdapter(),
        "video_gen": MockVideoGenAdapter(),
        "voice": MockVoiceAdapter(),
    }


@pytest.fixture
def compiled_graph(memory_checkpointer, mock_adapters):
    """Compiled graph with in-memory checkpointer and all-pass mock adapters."""
    return build_graph(
        llm=mock_adapters["llm"],
        image_gen=mock_adapters["image_gen"],
        video_gen=mock_adapters["video_gen"],
        voice=mock_adapters["voice"],
        checkpointer=memory_checkpointer,
    )


def make_graph(
    *,
    quality_fail_shot_ids: list[str] | None = None,
    fail_times: int = 1,
    checkpointer: MemorySaver | None = None,
):
    """
    Build a compiled graph with configurable quality failures.

    Parameters
    ----------
    quality_fail_shot_ids:
        Shot ids that should fail quality checks the first ``fail_times`` calls.
    fail_times:
        Number of consecutive failures to simulate per shot.
    checkpointer:
        Defaults to a fresh MemorySaver.
    """
    return build_graph(
        llm=MockLLMAdapter(
            quality_fail_shot_ids=quality_fail_shot_ids,
            fail_times=fail_times,
        ),
        image_gen=MockImageGenAdapter(),
        video_gen=MockVideoGenAdapter(),
        voice=MockVoiceAdapter(),
        checkpointer=checkpointer or MemorySaver(),
    )


def initial_state(topic: str = "a photon's journey from the sun to your eye") -> dict:
    """Return the minimal initial state dict for starting a run."""
    return {"topic": topic}


APPROVAL_SCRIPT = {"approved": True, "edits": []}
APPROVAL_FINAL = {"approved": True, "edits": []}
