"""Auto-generated stills for elon-musk-really-makes-his-money. Do not hardcode a person here;
character looks come from the project bible frozen below."""

from __future__ import annotations

PROP_BUDGET = {'THE_PADLOCKED_GLASS_PAY_STUB': 6}
SET_TOKENS = ['FILING_ROOM', 'LOCK_CABINET', 'TICKER_WALL', 'CAR_LOT', 'LAUNCH_DESK']

STYLE = "Clean flat 2D business documentary illustration in the established Behind The Business channel identity. Modern vector-like shapes, simple readable characters, simplified products and environments, crisp diagrams, subtle depth, limited shading, clean high-contrast palette, uncluttered compositions, clear information hierarchy, visually intuitive financial flows and business systems, consistent recurring locations and company elements. Educational but cinematic in composition. FILL THE ENTIRE FRAME edge to edge, no letterbox, no pillarbox, no black bars. Any on-image label, badge, sign, or diagram text must sit fully inside a 10 percent margin from every edge. Never place text flush with the top, bottom, or sides of the frame. Not photorealistic, not 3D, not anime, not painterly, not generic stock imagery. Accent this title with a midnight, pale-sand, and coral palette; keep the same clean flat 2D construction. Not photorealistic, not a photograph, not cinematic photography, not 3D, not Pixar, not anime, not manga, not watercolor, not oil painting, not hyper-detailed, not a superhero comic, not photomontage, not DSLR, not realistic skin texture. NO swastika, NO Nazi flag, NO SS runes, NO armbands, NO camps, NO gore, NO celebrity photoreal faces. No readable paragraphs of body copy, no watermarks, no captions overlaid on the frame unless the scene names a short on-screen label. Not a 3D corporate animation, not a stock-photo slideshow, not a Bloomberg terminal wall of numbers, not a photoreal product shot. Young adult in a plain gray hoodie holding a blank newspaper. Simple flat face. No logos. No readable type. Adult clerk in a gray vest and white shirt. Neat brown hair. Simple flat face. A padlocked glass pay stub on a lanyard. No logos. No readable type. Adult in a plain charcoal jacket. Short black hair. Simple flat face. No logos. No readable type."

STILLS: list[tuple[str, str, str]] = [
    ("close-up", "hero", "FILING_ROOM Long blank compensation table, one huge number in a glass sleeve, empty salary box, no logos, no readable paragraphs."),
    ("over-the-shoulder", "crowd", "LOCK_CABINET Two columns on a clean desk, a tall costume stack next to an empty realized tray, no logos, no readable type. The same oversized padlocked glass pay stub on a lanyard sits large in frame."),
    ("wide shot", "empty", "TICKER_WALL Clean business illustration of a filing table, a glass cabinet, and a blank ticker wall, same construction, no logos, no readable type."),
    ("top-down diagram", "empty", "CAR_LOT Plain option certificate with a large price stamp, no letters, no logos, heavy paper on a dark table."),
    ("medium shot", "empty", "LAUNCH_DESK Two blank ticker boards on a dark wall, one board brighter, small dish icon, no letters, no logos."),
    ("title card", "empty", "End card. Dark navy field. No people. Type added in assemble."),

]


def prompt_for(who: str, scene: str) -> str:
    extra = "STRICTLY NO people, NO faces, NO hands." if who == "empty" else (
        "Only named characters. Same cartoon construction every time."
    )
    return f"{STYLE} {extra} SCENE: {scene}"
