"""
human_review_final node — second non-bypassable human-review interrupt.

Execution pauses here after assembly and metadata generation.
The graph resumes only when the caller provides an explicit approval payload.
No code path may auto-approve or skip this gate.

Resume payload shape (passed as ``Command(resume=...)``):
    {
        "approved": True,
        "edits": [                          # optional
            {
                "field_path": "metadata.title",
                "new_value": "revised title",
                "note": "more compelling"
            }
        ]
    }
"""

from __future__ import annotations

from datetime import datetime, timezone

from langgraph.types import interrupt

from graph.state import HumanEdit, Metadata, PipelineState


async def human_review_final(state: PipelineState) -> dict:
    """
    Pause for final human review before publish.

    Applies any edits to metadata and logs them.
    Raises ValueError if the reviewer rejects (approved=False).

    Returns a partial state update: ``human_edits_log``, and possibly
    ``metadata`` if the reviewer supplied edits.
    """
    payload: dict = interrupt(
        {
            "gate": "human_review_final",
            "message": (
                "Final review before publish. "
                "Provide approved=True to publish or approved=False to abort. "
                "Optionally supply edits to metadata fields."
            ),
            "final_video_path": state.final_video_path,
            "metadata": state.metadata.model_dump(),
            "shot_summary": [
                {"id": s.id, "status": s.status, "retries": s.retry_count}
                for s in state.shot_list
            ],
        }
    )

    if not payload.get("approved", False):
        raise ValueError(
            "Human reviewer rejected at human_review_final gate. Aborting publish."
        )

    updates: dict = {}
    edit_records: list[HumanEdit] = []
    meta_overrides: dict = {}

    for edit in payload.get("edits", []):
        field_path: str = edit["field_path"]
        new_value = edit["new_value"]
        note: str = edit.get("note", "")

        # Support metadata sub-field edits (e.g. "metadata.title").
        if field_path.startswith("metadata."):
            sub_field = field_path[len("metadata."):]
            meta_overrides[sub_field] = new_value
        elif field_path == "metadata":
            meta_overrides = new_value if isinstance(new_value, dict) else {}

        edit_records.append(
            HumanEdit(
                gate="human_review_final",
                timestamp=datetime.now(timezone.utc),
                field_path=field_path,
                new_value=new_value,
                note=note,
            )
        )

    if meta_overrides:
        updated_meta = state.metadata.model_copy(update=meta_overrides)
        updates["metadata"] = updated_meta

    if edit_records:
        updates["human_edits_log"] = edit_records

    return updates
