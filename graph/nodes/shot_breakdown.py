"""
shot_breakdown node — turn the script into a structured shot list.

Each shot is tagged with a render mode (motion | static_pan, defaulting to
static_pan) and an assigned model.  The shot list is the primary cost lever:
only shots explicitly tagged 'motion' incur video-generation costs.
"""

from __future__ import annotations

from adapters.llm.base import LLMAdapter
from graph.state import PipelineState, Shot, ShotMode


async def shot_breakdown(state: PipelineState, llm: LLMAdapter) -> dict:
    """
    Build the shot list from the script.

    Returns a partial state update: ``shot_list``.
    """
    result = await llm.breakdown_shots(
        script=state.script,
        character_descriptor=state.character_refs.style_descriptor,
    )

    shots: list[Shot] = []
    for spec in result.shots:
        try:
            mode = ShotMode(spec.mode)
        except ValueError:
            # Unknown mode defaults to static_pan (cheap path).
            mode = ShotMode.static_pan

        shots.append(
            Shot(
                id=spec.id,
                prompt=spec.prompt,
                duration_seconds=spec.duration_seconds,
                mode=mode,
                assigned_model=spec.assigned_model,
            )
        )

    if not shots:
        raise ValueError("shot_breakdown produced an empty shot list.")

    return {"shot_list": shots}
