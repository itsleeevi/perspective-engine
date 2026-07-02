"""
ideate node — select or propose a topic for the pipeline run.

Invariant enforced here: no real, named, identifiable person may be the
subject of the video. Any topic that implies such a person is rejected with
a ValueError before the run proceeds.
"""

from __future__ import annotations

from graph.state import PipelineState
from graph.validation import assert_no_real_person


async def ideate(state: PipelineState) -> dict:
    """
    Validate the topic and produce a brief.

    In Phase 1 the topic is already set in the initial state; this node
    validates it and synthesises a one-sentence brief.  In Phase 2+ this
    node may also call the LLM to generate or refine the topic.

    Returns a partial state update: ``topic`` (unchanged) + ``brief``.
    """
    topic = state.topic.strip()
    if not topic:
        raise ValueError("topic must be set in the initial state before running ideate.")

    # Invariant: reject real, named, identifiable people as subjects.
    assert_no_real_person(topic)

    brief = (
        f"A perspective-shift narrative exploring '{topic}' "
        "from an angle that is hard to film conventionally."
    )
    return {"topic": topic, "brief": brief}
