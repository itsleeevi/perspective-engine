"""
generate_metadata node — produce title, description, tags, and thumbnail.

The description carries chapter timestamps, one per level, built from the same
shot durations the video was assembled from. YouTube turns a timestamp list
into a seekable chapter track, which is how viewers navigate a 25-minute
level-progression video.

Invariant enforced here: ``synthetic_content_disclosure`` is always set to
True before the run reaches publish, regardless of any prior value.
"""

from __future__ import annotations

from graph.script_fixture import is_title_beat, title_card_lines
from graph.state import CostEntry, Metadata, PipelineState, ShotStatus
from graph.validation import set_disclosure_flag

_DISCLOSURE_NOTE = (
    "This video is fictional and AI-generated. It depicts a composite, "
    "invented character and no real, named or identifiable person."
)


def _timestamp(seconds: float) -> str:
    total = int(seconds)
    hours, remainder = divmod(total, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


def _chapter_lines(state: PipelineState) -> list[str]:
    """
    Build ``0:00 Label`` chapter lines from the level title cards.

    YouTube only accepts the list as chapters if the first entry starts at
    0:00, so an intro entry is prepended when the video opens on narration.
    """
    active = [
        s
        for s in state.shot_list
        if s.status in (ShotStatus.approved, ShotStatus.escalated)
    ]

    lines: list[str] = []
    elapsed = 0.0
    for shot in active:
        if shot.is_title_card or is_title_beat(shot.prompt):
            line1, line2 = title_card_lines(shot.prompt)
            label = " ".join(part for part in (line1, line2) if part).strip()
            lines.append(f"{_timestamp(elapsed)} {label}")
        elapsed += shot.duration_seconds

    if not lines:
        return []
    if not lines[0].startswith("0:00"):
        lines.insert(0, "0:00 Intro")
    return lines


async def generate_metadata(state: PipelineState) -> dict:
    """
    Generate publish metadata and unconditionally set the disclosure flag.

    Returns a partial state update: ``metadata``, ``cost_log``.
    """
    chapters = _chapter_lines(state)

    description_parts = [state.brief.strip()] if state.brief.strip() else []
    if chapters:
        description_parts.append("Chapters:\n" + "\n".join(chapters))
    description_parts.append(_DISCLOSURE_NOTE)

    meta_dict = {
        "title": state.topic,
        "description": "\n\n".join(description_parts),
        "tags": ["perspective", "POV", "animated story", state.topic],
        "thumbnail_url": "",
        "synthetic_content_disclosure": False,  # set_disclosure_flag will override
    }

    # Invariant: always set to True.
    set_disclosure_flag(meta_dict)

    metadata = Metadata(**meta_dict)
    cost = CostEntry(node="generate_metadata", provider="local", amount_usd=0.0)
    return {"metadata": metadata, "cost_log": [cost]}
