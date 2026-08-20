"""
generate_character_refs node — produce the character reference sheet.

The reference sheet is the identity anchor for the entire run:

- The locked style descriptor (``graph.style.STYLE_DESCRIPTOR``) is repeated
  verbatim in every scene prompt, so the hero's design cannot drift between
  independently generated frames.
- The sheet image is what ``quality_gate`` compares each scene still against.
"""

from __future__ import annotations

from adapters.image_gen.base import ImageGenAdapter
from graph import style
from graph.state import CharacterRefs, CostEntry, PipelineState


async def generate_character_refs(
    state: PipelineState, image_gen: ImageGenAdapter
) -> dict:
    """
    Generate the character reference sheet and lock in the style descriptor.

    The descriptor is the canonical hero spec from ``graph.style`` rather than
    anything the provider invents, so it is byte-identical on every run and
    every shot prompt carries exactly the same identity. The sheet image is the
    visual reference the quality gate checks scene stills against.

    Returns a partial state update: ``character_refs``, ``cost_log``.
    """
    result = await image_gen.generate_reference_sheet(style.hero_description(state.topic))

    character_refs = CharacterRefs(
        sheet_image_urls=result.image_urls,
        style_descriptor=style.STYLE_DESCRIPTOR,
    )

    cost = CostEntry(
        node="generate_character_refs", provider="image_gen", amount_usd=result.cost_usd
    )
    return {"character_refs": character_refs, "cost_log": [cost]}
