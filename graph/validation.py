"""
Invariant checks shared across nodes.

These functions encode hard rules that are enforced in code rather than
documented. Raising ValueError from a node halts the run and surfaces
the violation clearly in the checkpointer / traceback.
"""

from __future__ import annotations

from graph.state import Shot, ShotMode


# ── Real-person guard ─────────────────────────────────────────────────────────

# A non-exhaustive list of trigger phrases that indicate a real, named,
# identifiable person is being used as a subject.  The ideate node calls
# assert_no_real_person; any topic matching these patterns must be rejected
# or fictionalized before the run continues.
#
# Phase 1: simple substring check against a known trigger list.
# Phase 2+: replace / augment with an LLM classifier call.
_REAL_PERSON_TRIGGERS: frozenset[str] = frozenset(
    [
        # Patterns that strongly suggest a real, named person
        "day in the life of [a-z]",  # kept as strings, matched with lower()
    ]
)

_REAL_PERSON_BLOCKLIST: frozenset[str] = frozenset(
    [
        # Explicit name fragments that must not appear as subjects.
        # Expand this list as needed; the LLM classifier in Phase 2+ is the
        # primary gate — this is a belt-and-suspenders defence for Phase 1.
        "elon musk",
        "donald trump",
        "joe biden",
        "taylor swift",
        "beyoncé",
        "mark zuckerberg",
        "jeff bezos",
    ]
)


def assert_no_real_person(topic: str) -> None:
    """
    Raise ValueError if the topic refers to a real, named, identifiable person.

    This is enforced at ideate; no run may proceed with a real-person subject.
    Callers must fictionalize or make the subject composite before continuing.
    """
    lower = topic.lower()
    for name in _REAL_PERSON_BLOCKLIST:
        if name in lower:
            raise ValueError(
                f"Topic '{topic}' refers to a real, identifiable person "
                f"(matched: '{name}'). Fictionalize or make the subject "
                "composite before proceeding."
            )


# ── Still-first rule ──────────────────────────────────────────────────────────


def assert_still_before_video(shot: Shot) -> None:
    """
    Raise ValueError if a motion shot has no derived still.

    Enforced inside generate_shots before any video-generation call.
    The pattern is: locked identity → per-shot still → clip.
    Direct text-to-video for character shots is never permitted.
    """
    if shot.mode == ShotMode.motion and not shot.still_url:
        raise ValueError(
            f"Shot '{shot.id}' is tagged 'motion' but has no derived still. "
            "Generate a per-shot still from the character reference sheet "
            "before calling the video adapter."
        )


# ── Disclosure flag ───────────────────────────────────────────────────────────


def set_disclosure_flag(metadata_dict: dict) -> dict:
    """
    Ensure the synthetic-content disclosure flag is set to True.

    Called by generate_metadata; must be called before publish.
    Returns the mutated dict for convenience.
    """
    metadata_dict["synthetic_content_disclosure"] = True
    return metadata_dict
