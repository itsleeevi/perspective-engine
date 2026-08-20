"""
human_review_images node — non-bypassable interrupt after still generation.

Pauses once every ``process_shot`` sub-execution has finished, before
voiceover and assembly. The reviewer inspects stills and either approves
the set or lists shot ids to regenerate. Regeneration happens inside this
node (not as a graph re-dispatch) so the fan-in barrier count is untouched.

LangGraph replays a node from the top on each resume: previously resolved
``interrupt()`` calls return their cached resume values, so a ``while``
loop that interrupts, regenerates, and interrupts again is the supported
pattern for a multi-round review.

Resume payload shape (passed as ``Command(resume=...)``):
    {
        "approved": True,
        "regenerate_shot_ids": ["shot_003"]   # empty list = accept all
    }
"""

from __future__ import annotations

from datetime import datetime, timezone

from langgraph.types import interrupt

from adapters.image_gen.base import ImageGenAdapter
from graph.config import MAX_MANUAL_REGENERATIONS
from graph.state import CostEntry, HumanEdit, PipelineState, Shot, ShotStatus


def _coerce(state) -> PipelineState:
    if isinstance(state, PipelineState):
        return state
    return PipelineState.model_validate(state)


async def human_review_images(state, image_gen: ImageGenAdapter) -> dict:
    """
    Pause for human review of generated stills; regenerate flagged shots.

    Raises ValueError if the reviewer rejects (approved=False).
    Returns a partial state update: ``shot_list``, and possibly
    ``human_edits_log`` / ``cost_log`` if any shots were regenerated.
    """
    state = _coerce(state)
    char_refs = state.character_refs
    shots: dict[str, Shot] = {s.id: s for s in state.shot_list}
    edit_records: list[HumanEdit] = []
    cost_entries: list[CostEntry] = []

    while True:
        payload: dict = interrupt(
            {
                "gate": "human_review_images",
                "message": (
                    "Review generated stills. Provide approved=True with an empty "
                    "regenerate_shot_ids to continue, or list shot ids to redo — "
                    "the gate will re-interrupt with the fresh images."
                ),
                "shot_list": [s.model_dump() for s in shots.values()],
            }
        )

        if not payload.get("approved", False):
            raise ValueError(
                "Human reviewer rejected the stills at human_review_images gate."
            )

        to_regen = payload.get("regenerate_shot_ids") or []
        if not to_regen:
            break

        for shot_id in to_regen:
            shot = shots.get(shot_id)
            if shot is None or shot.is_title_card:
                continue
            if shot.manual_regen_count >= MAX_MANUAL_REGENERATIONS:
                continue

            result = await image_gen.derive_still(
                shot_prompt=shot.prompt,
                sheet_image_urls=char_refs.sheet_image_urls,
                style_descriptor=char_refs.style_descriptor,
                attempt=shot.retry_count + shot.manual_regen_count + 1,
            )
            shots[shot_id] = shot.model_copy(
                update={
                    "still_url": result.still_url,
                    "manual_regen_count": shot.manual_regen_count + 1,
                    "status": ShotStatus.approved,
                }
            )
            edit_records.append(
                HumanEdit(
                    gate="human_review_images",
                    timestamp=datetime.now(timezone.utc),
                    field_path=f"shot_list[{shot_id}].still_url",
                    new_value=result.still_url,
                    note="manual regeneration",
                )
            )
            cost_entries.append(
                CostEntry(
                    node="human_review_images:still",
                    provider="image_gen",
                    amount_usd=result.cost_usd,
                )
            )

    updates: dict = {"shot_list": list(shots.values())}
    if edit_records:
        updates["human_edits_log"] = edit_records
    if cost_entries:
        updates["cost_log"] = cost_entries
    return updates
