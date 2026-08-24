"""Auto-generated stills for mcdonald-s-really-makes-money. Do not hardcode a person here;
character looks come from the project bible frozen below."""

from __future__ import annotations

PROP_BUDGET = {'THE_NUMBERED_BRASS_STORE_KEY': 6}
SET_TOKENS = ['DRIVE_THRU', 'TRAY_COUNTER', 'LEASE_OFFICE', 'LAB_KITCHEN', 'MAP_TABLE']

STYLE = "Clean flat 2D business documentary illustration in the established Behind The Business channel identity. Modern vector-like shapes, simple readable characters, simplified products and environments, crisp diagrams, subtle depth, limited shading, clean high-contrast palette, uncluttered compositions, clear information hierarchy, visually intuitive financial flows and business systems, consistent recurring locations and company elements. Educational but cinematic in composition. FILL THE ENTIRE FRAME edge to edge, no letterbox, no pillarbox, no black bars. Any on-image label, badge, sign, or diagram text must sit fully inside a 10 percent margin from every edge. Never place text flush with the top, bottom, or sides of the frame. Not photorealistic, not 3D, not anime, not painterly, not generic stock imagery. Accent this title with a deep ink, silver, and electric-blue palette; keep the same clean flat 2D construction. Not photorealistic, not a photograph, not cinematic photography, not 3D, not Pixar, not anime, not manga, not watercolor, not oil painting, not hyper-detailed, not a superhero comic, not photomontage, not DSLR, not realistic skin texture. NO swastika, NO Nazi flag, NO SS runes, NO armbands, NO camps, NO gore, NO celebrity photoreal faces. No readable paragraphs of body copy, no watermarks, no captions overlaid on the frame unless the scene names a short on-screen label. Not a 3D corporate animation, not a stock-photo slideshow, not a Bloomberg terminal wall of numbers, not a photoreal product shot. Teen in a plain gray hoodie holding a blank paper food bag. Simple flat face. No logos. No readable type. Adult operator in a plain navy polo and khaki pants. Short black hair. Oversized brass key on a blank numbered tag at the belt. Simple flat face. No logos. No readable type. Young crew in a plain charcoal visor and polo. No logos. Simple flat face. No readable type."

STILLS: list[tuple[str, str, str]] = [
    ("wide shot", "crowd", "DRIVE_THRU Night drive-thru window, paper bag passing to a car, till glowing, no logos, no readable type."),
    ("medium shot", "hero", "TRAY_COUNTER Night drive-thru window, paper bag passing to a car, till glowing, no logos, no readable type. The same oversized brass key on a blank numbered tag sits large in frame."),
    ("close-up", "empty", "LEASE_OFFICE A thick kraft envelope standing taller than a thin rubber stamp, clean desk, no logos, no readable paragraphs."),
    ("over-the-shoulder", "empty", "LAB_KITCHEN A thick kraft envelope standing taller than a thin rubber stamp, clean desk, no logos, no readable paragraphs."),
    ("top-down diagram", "empty", "MAP_TABLE Lease office key rack, rows of blank numbered tags, one hook empty, no logos, no readable contracts."),
    ("title card", "empty", "End card. Dark navy field. No people. Type added in assemble."),

]


def prompt_for(who: str, scene: str) -> str:
    extra = "STRICTLY NO people, NO faces, NO hands." if who == "empty" else (
        "Only named characters. Same cartoon construction every time."
    )
    return f"{STYLE} {extra} SCENE: {scene}"
