"""
generate_character_refs node — produce the character reference sheet.

The reference sheet is the identity anchor for the entire run.  Every
subsequent shot is generated from a still derived from this sheet.

Produces:
- A set of reference images covering multiple angles / expressions / lighting.
- A persistent style descriptor (with a deliberately distinctive detail)
  appended to every shot prompt.
"""

from __future__ import annotations

from adapters.image_gen.base import ImageGenAdapter
from graph.state import CharacterRefs, CostEntry, PipelineState


_CHARACTER_DESCRIPTION_TEMPLATE = (
    "Fictional composite character for the story: '{topic}'. "
    "Not based on any real, named, identifiable person. "
    "Expressive, distinctive, memorable."
)


async def generate_character_refs(
    state: PipelineState, image_gen: ImageGenAdapter
) -> dict:
    """
    Generate the character reference sheet and style descriptor.

    Returns a partial state update: ``character_refs``, ``cost_log``.
    """
    description = _CHARACTER_DESCRIPTION_TEMPLATE.format(topic=state.topic)
    result = await image_gen.generate_reference_sheet(description)

    character_refs = CharacterRefs(
        sheet_image_urls=result.image_urls,
        style_descriptor=result.style_descriptor,
    )

    cost = CostEntry(node="generate_character_refs", provider="image_gen", amount_usd=0.0)
    return {"character_refs": character_refs, "cost_log": [cost]}
