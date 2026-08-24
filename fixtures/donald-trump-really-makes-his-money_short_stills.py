"""Auto-generated stills for donald-trump-really-makes-his-money. Do not hardcode a person here;
character looks come from the project bible frozen below."""

from __future__ import annotations

PROP_BUDGET = {'THE_BLANK_GOLD_HOTEL_NAMEPLATE': 6}
SET_TOKENS = ['NAMEPLATE_SHOP', 'FILING_ROOM', 'TOWER_LOBBY', 'STUDIO_SET', 'GOLF_DESK', 'TICKER_WALL']

STYLE = "Clean flat 2D business documentary illustration in the established Behind The Business channel identity. Modern vector-like shapes, simple readable characters, simplified products and environments, crisp diagrams, subtle depth, limited shading, clean high-contrast palette, uncluttered compositions, clear information hierarchy, visually intuitive financial flows and business systems, consistent recurring locations and company elements. Educational but cinematic in composition. FILL THE ENTIRE FRAME edge to edge, no letterbox, no pillarbox, no black bars. Any on-image label, badge, sign, or diagram text must sit fully inside a 10 percent margin from every edge. Never place text flush with the top, bottom, or sides of the frame. Not photorealistic, not 3D, not anime, not painterly, not generic stock imagery. Accent this title with a graphite, paper-white, and signal-orange palette; keep the same clean flat 2D construction. Not photorealistic, not a photograph, not cinematic photography, not 3D, not Pixar, not anime, not manga, not watercolor, not oil painting, not hyper-detailed, not a superhero comic, not photomontage, not DSLR, not realistic skin texture. NO swastika, NO Nazi flag, NO SS runes, NO armbands, NO camps, NO gore, NO celebrity photoreal faces. No readable paragraphs of body copy, no watermarks, no captions overlaid on the frame unless the scene names a short on-screen label. Not a 3D corporate animation, not a stock-photo slideshow, not a Bloomberg terminal wall of numbers, not a photoreal product shot. Adult clerk in a gray vest and white shirt. Neat brown hair. Simple flat face. A blank gold hotel nameplate on a lanyard. No logos. No readable type. Young adult in a plain gray hoodie holding a blank magazine. Simple flat face. No logos. No readable type."

STILLS: list[tuple[str, str, str]] = [
    ("wide shot", "crowd", "NAMEPLATE_SHOP Fat unlabeled binder standing taller than a thin invoice on a long table, cool gray light, no logos, no readable paragraphs."),
    ("medium shot", "hero", "FILING_ROOM Fat unlabeled binder standing taller than a thin invoice on a long table, cool gray light, no logos, no readable paragraphs. THE_BLANK_GOLD_HOTEL_NAMEPLATE the same oversized blank gold hotel nameplate with no letters sits large in frame."),
    ("close-up", "empty", "TOWER_LOBBY Workshop pegboard of blank gold plates with no letters, one plate hanging from a peg, warm lamp, no logos."),
    ("over-the-shoulder", "empty", "STUDIO_SET Workshop pegboard of blank gold plates with no letters, one plate hanging from a peg, warm lamp, no logos."),
    ("low angle", "empty", "GOLF_DESK One blank ticker board, a tiny sales bar beside a tall ownership block, no letters, no logos."),
    ("wide shot", "empty", "TICKER_WALL Fat unlabeled binder standing taller than a thin invoice on a long table, cool gray light, no logos, no readable paragraphs."),
    ("title card", "empty", "End card. Dark navy field. No people. Type added in assemble."),

]


def prompt_for(who: str, scene: str) -> str:
    extra = "STRICTLY NO people, NO faces, NO hands." if who == "empty" else (
        "Only named characters. Same cartoon construction every time."
    )
    return f"{STYLE} {extra} SCENE: {scene}"
