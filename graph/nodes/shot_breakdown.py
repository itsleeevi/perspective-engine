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

    # Honour the optional shot cap (e.g. --shots 1 for cheap smoke tests).
    if state.max_shots is not None and state.max_shots > 0:
        shots = shots[: state.max_shots]

    # --static mode: override all shots to static_pan so no video-gen calls
    # are made. Costs only FLUX stills + Claude + ElevenLabs (~$0.05/run).
    if state.static_only:
        shots = [
            s.model_copy(update={"mode": ShotMode.static_pan, "assigned_model": "fal-ai/flux/dev"})
            for s in shots
        ]

    return {"shot_list": shots}
