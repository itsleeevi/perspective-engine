"""
assemble node — compose clips, stills, audio, and captions into the final cut.

In Phase 1 this is a mock that records what would be assembled and writes
a placeholder path.  Phase 2+ will invoke Remotion programmatically.
"""

from __future__ import annotations

from graph.assets import local_asset_url
from graph.state import CostEntry, PipelineState, ShotMode, ShotStatus


async def assemble(state: PipelineState) -> dict:
    """
    Mock assembly step.

    Returns a partial state update: ``final_video_path``, ``cost_log``.
    """
    approved = [
        s for s in state.shot_list
        if s.status in (ShotStatus.approved, ShotStatus.escalated)
    ]

    # Phase 1: produce a placeholder path summarising what would be composed.
    slug = state.topic.lower().replace(" ", "_")[:40]
    output_path = local_asset_url(f"output/{slug}_final.mp4")

    # Log what would be assembled (useful for debugging / test assertions).
    motion_count = sum(1 for s in approved if s.mode == ShotMode.motion)
    static_count = len(approved) - motion_count

    _ = (
        f"[assemble] {len(approved)} shots "
        f"({motion_count} motion, {static_count} static_pan), "
        f"voiceover={state.voiceover_url!r}, "
        f"output={output_path!r}"
    )

    cost = CostEntry(node="assemble", provider="local", amount_usd=0.0)
    return {"final_video_path": output_path, "cost_log": [cost]}
