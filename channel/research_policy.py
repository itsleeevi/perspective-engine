"""Research traceability policy — every claim must be sourceable."""

from __future__ import annotations

from channel.originality_policy import RESEARCH_SOURCE_PRIORITY

# Internal claim fields agents must fill on every important fact.
CLAIM_TRACE_FIELDS = (
    "claim_id",
    "claim",
    "kind",
    "sources",
    "source_type",
    "confidence",
    "quote",
    "is_direct_quote",
)

FORBIDDEN_INVENTIONS = (
    "quotes without verified wording",
    "private conversations without evidence",
    "diary entries that cannot be sourced",
    "letters that cannot be sourced",
    "motives presented as facts without evidence",
    "meetings or events with no record",
)

INSUFFICIENT_EVIDENCE_PHRASE = (
    "We cannot know exactly what they privately believed, but their letters, "
    "public statements, and decisions give us a fairly clear picture."
)

__all__ = [
    "CLAIM_TRACE_FIELDS",
    "FORBIDDEN_INVENTIONS",
    "INSUFFICIENT_EVIDENCE_PHRASE",
    "RESEARCH_SOURCE_PRIORITY",
]
