"""
Single source of truth for pipeline state.

All nodes read from and write partial updates against PipelineState.
No ad hoc dictionaries are passed between nodes.
"""

from __future__ import annotations

import operator
from datetime import datetime, timezone
from enum import Enum
from typing import Annotated, Any

from pydantic import BaseModel, Field


class ShotMode(str, Enum):
    """Render mode for a shot. static_pan is the default (cheap path)."""

    motion = "motion"
    static_pan = "static_pan"


class ShotStatus(str, Enum):
    """Processing status for an individual shot."""

    pending = "pending"
    generating = "generating"
    quality_check = "quality_check"
    approved = "approved"
    failed = "failed"
    escalated = "escalated"


class Shot(BaseModel):
    """A single shot entry in the shot list."""

    id: str
    prompt: str
    duration_seconds: float = 5.0
    mode: ShotMode = ShotMode.static_pan
    assigned_model: str = ""

    # The narration beat this shot illustrates. Kept on the shot so the voice
    # adapter and the assembler work off one ordering, and so each shot's
    # on-screen duration can be set from its own measured audio length.
    narration: str = ""

    # True for level title cards, which are rendered locally instead of being
    # sent to an image model.
    is_title_card: bool = False

    # Asset URLs written by generate_shots
    still_url: str = ""
    clip_url: str = ""

    status: ShotStatus = ShotStatus.pending
    retry_count: int = 0
    escalated: bool = False

    # Human-triggered regenerations at the image-review gate. Distinct from
    # retry_count so automatic quality-gate retries and manual redos don't
    # share a budget, and so derive_still gets a unique cache-busting attempt.
    manual_regen_count: int = 0

    # Populated by quality_gate: human-readable reason for last failure
    quality_failure_reason: str = ""


class CharacterRefs(BaseModel):
    """Identity anchor produced by generate_character_refs."""

    # URLs of reference-sheet images (multiple angles / expressions)
    sheet_image_urls: list[str] = Field(default_factory=list)

    # Persistent text descriptor appended to every shot prompt.
    # Includes at least one deliberately distinctive identifying detail.
    style_descriptor: str = ""

    # Per-shot derived still URLs, keyed by shot id.
    # Populated by generate_shots before any video call.
    per_shot_stills: dict[str, str] = Field(default_factory=dict)


class HumanEdit(BaseModel):
    """A single edit record written at a review gate."""

    gate: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    field_path: str
    old_value: Any = None
    new_value: Any = None
    note: str = ""


class CostEntry(BaseModel):
    """One cost record written by a node."""

    node: str
    provider: str
    amount_usd: float
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Metadata(BaseModel):
    """Video metadata prepared for publish."""

    title: str = ""
    description: str = ""
    tags: list[str] = Field(default_factory=list)
    thumbnail_url: str = ""

    # Invariant: always True at publish; set by generate_metadata.
    synthetic_content_disclosure: bool = False


# ── Reducer for shot_list ─────────────────────────────────────────────────────


def _merge_shots(existing: list[Shot], update: list[Shot]) -> list[Shot]:
    """
    Fan-out reducer: merges per-shot updates back into the shot list.

    Incoming updates carry partial Shot objects (same id).  An update for an
    id that already exists replaces the old entry; an update for a new id is
    appended.  Order in the output mirrors the original list, with new entries
    appended in the order they arrive.
    """
    by_id: dict[str, Shot] = {s.id: s for s in existing}
    for shot in update:
        by_id[shot.id] = shot
    # Preserve original ordering; append genuinely new ids at the end.
    seen: set[str] = set()
    result: list[Shot] = []
    for s in existing:
        result.append(by_id[s.id])
        seen.add(s.id)
    for s in update:
        if s.id not in seen:
            result.append(by_id[s.id])
            seen.add(s.id)
    return result


class PipelineState(BaseModel):
    """
    Complete state for one pipeline run. Threaded through every node.
    Nodes receive the full state and return a partial dict of updates.
    """

    # ── Inputs ────────────────────────────────────────────────────────────────
    topic: str = ""
    brief: str = ""
    # Optional shot count cap. None = use all shots from breakdown.
    # Set to a small number (e.g. 1) for cheap smoke tests.
    max_shots: int | None = None
    # Force all shots to static_pan (no Seedance video calls).
    # Combined with max_shots=1: ~$0.05/run after the first run.
    static_only: bool = True

    # Path to a script fixture JSON. When set (or auto-resolved from the topic)
    # the script comes from the fixture and no script LLM call is made.
    script_fixture_path: str = ""

    # Cap the run to the first N levels of the fixture. 0 = all levels.
    max_levels: int = 0

    # Whether to speak the fixture/LLM script's cold-open hook line before
    # Level One's title card. Some reference formats open on a hook; others
    # cut straight to "Level One" with no preamble. Default True preserves
    # existing behaviour; set False to start directly on Level One.
    include_hook: bool = True

    # Intended spoken runtime of the finished video, in minutes. 0 = let the
    # script writer choose. This is applied when the script is *written*, by
    # sizing level count and words per level to a word budget — capping the
    # script afterwards would cut off the final level, which is the one that
    # closes the loop back to the beginning. Ignored on the fixture path,
    # where the script is already written (use max_levels there).
    target_minutes: float = 0.0

    # Whether to escalate the hero's clothing/bearing across title-card levels
    # (rank insignia, posture). Off for non-career formats — e.g. a detention
    # explainer — where late-career "senior uniform" notes would contradict
    # the scene's orange jumpsuit.
    hero_career_progression: bool = True

    # Final video frame height; width is derived at 16:9. 0 = the project
    # default in graph.style (2160, i.e. 4K).
    output_height: int = 0

    # ── Script ────────────────────────────────────────────────────────────────
    # List of scene beats. The first beat is the hook, unless include_hook was
    # False, in which case the first beat is Level One's title card.
    script: list[str] = Field(default_factory=list)

    # ── Shots ─────────────────────────────────────────────────────────────────
    # LangGraph uses the annotated reducer to merge fan-out partial updates.
    shot_list: Annotated[list[Shot], _merge_shots] = Field(default_factory=list)

    # ── Character identity ────────────────────────────────────────────────────
    character_refs: CharacterRefs = Field(default_factory=CharacterRefs)

    # ── Final assets ──────────────────────────────────────────────────────────
    voiceover_url: str = ""
    music_url: str = ""
    final_video_path: str = ""

    # ── Publish metadata ──────────────────────────────────────────────────────
    metadata: Metadata = Field(default_factory=Metadata)

    # ── Audit logs ────────────────────────────────────────────────────────────
    cost_log: Annotated[list[CostEntry], operator.add] = Field(default_factory=list)
    human_edits_log: Annotated[list[HumanEdit], operator.add] = Field(
        default_factory=list
    )

    # ── Publish cadence guard ─────────────────────────────────────────────────
    # ISO-format timestamp of the last successful publish, stored in state so
    # it persists across the checkpointer without needing external state.
    last_published_at: str = ""
