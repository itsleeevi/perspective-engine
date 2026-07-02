"""
generate_voiceover node — synthesise narration aligned to shot timings.

Runs after all shots have cleared the quality gate (fan-in complete).
Only approved and escalated shots contribute to the voiceover timing.
"""

from __future__ import annotations

from adapters.voice.base import VoiceAdapter
from graph.state import CostEntry, PipelineState, ShotStatus


async def generate_voiceover(state: PipelineState, voice: VoiceAdapter) -> dict:
    """
    Call the TTS adapter with the script beats and shot durations.

    Returns a partial state update: ``voiceover_url``, ``cost_log``.
    """
    # Only include shots that completed (approved or escalated).
    active_shots = [
        s for s in state.shot_list
        if s.status in (ShotStatus.approved, ShotStatus.escalated)
    ]
    durations = [s.duration_seconds for s in active_shots]

    result = await voice.synthesize(
        script_beats=state.script,
        shot_durations=durations,
    )
    cost = CostEntry(node="generate_voiceover", provider="voice", amount_usd=0.0)
    return {"voiceover_url": result.audio_url, "cost_log": [cost]}
