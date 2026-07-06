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


def _character_description(topic: str) -> str:
    """
    Derive a visually grounded character description from the topic.

    The description is used to generate a reference sheet that anchors
    every shot's visual identity. It must be:
    - Visually concrete (something FLUX can render as a portrait)
    - Fictional / composite — no real, named, identifiable people
    - Specific enough that all shots feel like the same "character"

    For abstract or non-human topics (a photon, a river, gravity) we
    personify the subject as a stylised humanoid figure whose appearance
    metaphorically reflects the topic.
    """
    return (
        f"A fictional, visually distinctive protagonist embodying the concept of '{topic}'. "
        "Stylised humanoid figure. Not based on any real person. "
        "Expressive face, otherworldly quality, memorable silhouette. "
        "Consistent appearance across all angles and lighting conditions."
    )


async def generate_character_refs(
    state: PipelineState, image_gen: ImageGenAdapter
) -> dict:
    """
    Generate the character reference sheet and style descriptor.

    Returns a partial state update: ``character_refs``, ``cost_log``.
    """
    description = _character_description(state.topic)
    result = await image_gen.generate_reference_sheet(description)

    character_refs = CharacterRefs(
        sheet_image_urls=result.image_urls,
        style_descriptor=result.style_descriptor,
    )

    cost = CostEntry(node="generate_character_refs", provider="image_gen", amount_usd=0.0)
    return {"character_refs": character_refs, "cost_log": [cost]}
