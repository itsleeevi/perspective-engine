"""
generate_voiceover node — synthesise narration and lock the shot timings to it.

Runs after all shots have cleared the quality gate (fan-in complete).

This node owns audio/visual sync. Shot durations up to this point are
word-count estimates; real narration never matches an estimate, and the error
compounds over a hundred shots into minutes of drift. So the adapter reports
the measured duration of each beat, and each shot's on-screen time is rewritten
to its own beat's length. Every image then changes exactly on its narration
boundary, and the sum of shot durations equals the audio length by
construction.
"""

from __future__ import annotations

from adapters.voice.base import VoiceAdapter
from graph.state import CostEntry, PipelineState, ShotStatus


async def generate_voiceover(state: PipelineState, voice: VoiceAdapter) -> dict:
    """
    Synthesise the narration and retime shots to the measured audio.

    Returns a partial state update: ``voiceover_url``, ``shot_list``,
    ``cost_log``.
    """
    # Only shots that completed (approved or escalated) reach the video, so
    # only their narration is spoken.
    active_shots = [
        s
        for s in state.shot_list
        if s.status in (ShotStatus.approved, ShotStatus.escalated)
    ]
    if not active_shots:
        raise ValueError("generate_voiceover reached with no completed shots.")

    result = await voice.synthesize(
        script_beats=[s.narration for s in active_shots],
        shot_durations=[s.duration_seconds for s in active_shots],
    )

    updated = []
    for shot, measured in zip(active_shots, result.beat_durations, strict=False):
        updated.append(
            shot.model_copy(update={"duration_seconds": round(measured, 3)})
        )
    # Adapters that cannot measure per-beat timing (mocks) return no durations;
    # those shots keep their estimates.
    updated.extend(active_shots[len(updated) :])

    cost = CostEntry(
        node="generate_voiceover", provider="voice", amount_usd=result.cost_usd
    )
    return {
        "voiceover_url": result.audio_url,
        "shot_list": updated,
        "cost_log": [cost],
    }
