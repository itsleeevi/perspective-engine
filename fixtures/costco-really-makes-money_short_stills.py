"""Auto-generated stills for costco-really-makes-money. Do not hardcode a person here;
character looks come from the project bible frozen below."""

from __future__ import annotations

PROP_BUDGET = {'THE_GOLD_CARD': 6}
SET_TOKENS = ['EXIT', 'AISLE', 'DOOR', 'MEMBERSHIP_DESK', 'DEPOT', 'GAS', 'KIRKLAND_SHELF', 'WORLD_MAP']

STYLE = "Clean flat 2D business documentary illustration in the established Behind The Business channel identity. Modern vector-like shapes, simple readable characters, simplified products and environments, crisp diagrams, subtle depth, limited shading, clean high-contrast palette, uncluttered compositions, clear information hierarchy, visually intuitive financial flows and business systems, consistent recurring locations and company elements. Educational but cinematic in composition. FILL THE ENTIRE FRAME edge to edge, no letterbox, no pillarbox, no black bars. Any on-image label, badge, sign, or diagram text must sit fully inside a 10 percent margin from every edge. Never place text flush with the top, bottom, or sides of the frame. Not photorealistic, not 3D, not anime, not painterly, not generic stock imagery. Accent this title with a slate, bright-white, and gold-line palette; keep the same clean flat 2D construction. Not photorealistic, not a photograph, not cinematic photography, not 3D, not Pixar, not anime, not manga, not watercolor, not oil painting, not hyper-detailed, not a superhero comic, not photomontage, not DSLR, not realistic skin texture. NO swastika, NO Nazi flag, NO SS runes, NO armbands, NO camps, NO gore, NO celebrity photoreal faces. No readable paragraphs of body copy, no watermarks, no captions overlaid on the frame unless the scene names a short on-screen label. Not a 3D corporate animation, not a stock-photo slideshow, not a Bloomberg terminal wall of numbers, not a photoreal product shot. CHARACTER shopper: adult with short chestnut crop hair, simple oval cartoon face, slate crewneck sweater over a white collar, flat 2D vector, NOT photoreal CHARACTER greeter: adult, short salt-and-pepper hair, simple cartoon face, charcoal vest over a pale shirt, no logos, flat 2D vector, NOT photoreal CHARACTER clerk: younger adult, dark hair in a short ponytail, simple cartoon face, pale blue smock over a white shirt, no logos, flat 2D vector, NOT photoreal"

STILLS: list[tuple[str, str, str]] = [
    ("medium shot", "hero", "DOOR Shopper in a slate sweater holds a gold-toned card at a warehouse door. No logos."),
    ("close-up", "empty", "DOOR THE_GOLD_CARD A bright gold membership card, large in frame, high contrast, the same simple rounded rectangle every time, no letters on the plastic hits a simple door scanner, large in frame. No logos."),
    ("wide shot", "empty", "AISLE Pallet stacks under metal racks. Prices feel low. No people. No logos."),
    ("wide shot", "empty", "MEMBERSHIP_DESK A short gold bar next to a tall ice-white bar. No axis labels. No logos."),
    ("close-up", "empty", "EXIT A long blank cream receipt at an empty exit lane. No readable paragraphs. No logos."),
    ("close-up", "empty", "DOOR THE_GOLD_CARD A bright gold membership card, large in frame, high contrast, the same simple rounded rectangle every time, no letters on the plastic at the door, large in frame. No logos."),
    ("title card", "empty", "End card. Dark navy field. No people. Type added in assemble."),

]


def prompt_for(who: str, scene: str) -> str:
    extra = "STRICTLY NO people, NO faces, NO hands." if who == "empty" else (
        "Only named characters. Same cartoon construction every time."
    )
    return f"{STYLE} {extra} SCENE: {scene}"
