"""
generate_metadata node — produce title, description, tags, and thumbnail.

Invariant enforced here: ``synthetic_content_disclosure`` is always set to
True before the run reaches publish, regardless of any prior value.
"""

from __future__ import annotations

from graph.state import CostEntry, Metadata, PipelineState
from graph.validation import set_disclosure_flag


async def generate_metadata(state: PipelineState) -> dict:
    """
    Generate publish metadata and unconditionally set the disclosure flag.

    Returns a partial state update: ``metadata``, ``cost_log``.
    """
    meta_dict = {
        "title": f"A New Perspective: {state.topic}",
        "description": state.brief,
        "tags": ["perspective", "AI-generated", state.topic],
        "thumbnail_url": "",
        "synthetic_content_disclosure": False,  # set_disclosure_flag will override
    }

    # Invariant: always set to True.
    set_disclosure_flag(meta_dict)

    metadata = Metadata(**meta_dict)
    cost = CostEntry(node="generate_metadata", provider="local", amount_usd=0.0)
    return {"metadata": metadata, "cost_log": [cost]}
