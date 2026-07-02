"""
human_review_script node — first non-bypassable human-review interrupt.

Execution pauses here. The graph resumes only when the caller provides an
explicit resume payload via the checkpointer.  No code path may auto-approve
or skip this gate.

Resume payload shape (passed as ``Command(resume=...)``):
    {
        "approved": True,
        "edits": [                          # optional list of edits
            {
                "field_path": "script[0]",
                "new_value": "revised hook line",
                "note": "tightened the hook"
            }
        ]
    }
"""

from __future__ import annotations

from datetime import datetime, timezone

from langgraph.types import interrupt

from graph.state import HumanEdit, PipelineState


async def human_review_script(state: PipelineState) -> dict:
    """
    Pause for human review of the script and shot list.

    Applies any edits from the resume payload to state and logs them.
    Raises ValueError if the reviewer rejects (approved=False).

    Returns a partial state update: ``human_edits_log`` (and possibly
    ``script`` / ``shot_list`` if the reviewer supplied edits).
    """
    payload: dict = interrupt(
        {
            "gate": "human_review_script",
            "message": (
                "Review the script and shot list. "
                "Provide approved=True to continue or approved=False to abort. "
                "Optionally supply edits as a list of {field_path, new_value, note}."
            ),
            "script": state.script,
            "shot_list": [s.model_dump() for s in state.shot_list],
        }
    )

    if not payload.get("approved", False):
        raise ValueError(
            "Human reviewer rejected the script at human_review_script gate."
        )

    updates: dict = {}
    edit_records: list[HumanEdit] = []

    for edit in payload.get("edits", []):
        field_path: str = edit["field_path"]
        new_value = edit["new_value"]
        note: str = edit.get("note", "")

        # Apply simple top-level field edits; complex paths (e.g. shot_list[0].prompt)
        # are handled by callers composing a full replacement list.
        if field_path == "script":
            updates["script"] = new_value
        elif field_path == "shot_list":
            updates["shot_list"] = new_value

        edit_records.append(
            HumanEdit(
                gate="human_review_script",
                timestamp=datetime.now(timezone.utc),
                field_path=field_path,
                new_value=new_value,
                note=note,
            )
        )

    if edit_records:
        updates["human_edits_log"] = edit_records

    return updates
