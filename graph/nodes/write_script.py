"""
write_script node — generate the narrative script from topic and brief.

The first beat in the returned script is always the hook (opening line).
"""

from __future__ import annotations

from adapters.llm.base import LLMAdapter
from graph.state import PipelineState


async def write_script(state: PipelineState, llm: LLMAdapter) -> dict:
    """
    Call the LLM to produce an ordered list of script beats.

    beats[0] is always the hook.

    Returns a partial state update: ``script``.
    """
    result = await llm.write_script(topic=state.topic, brief=state.brief)
    beats = result.beats
    if not beats:
        raise ValueError("LLM returned an empty script; at least a hook line is required.")
    return {"script": beats}
