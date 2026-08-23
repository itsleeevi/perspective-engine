"""Auto-generated stills for visa-really-makes-money. Do not hardcode a person here;
character looks come from the project bible frozen below."""

from __future__ import annotations

PROP_BUDGET = {'THE_AUTHORIZATION_PULSE': 6}
SET_TOKENS = ['CHECKOUT', 'FOUR_DESKS', 'NETWORK_ROOM', 'BANK_OFFICE', 'PAPER_STACK', 'WORLD_MAP']

STYLE = "Clean flat 2D business documentary illustration in the established Behind The Business channel identity. Modern vector-like shapes, simple readable characters, simplified products and environments, crisp diagrams, subtle depth, limited shading, clean high-contrast palette, uncluttered compositions, clear information hierarchy, visually intuitive financial flows and business systems, consistent recurring locations and company elements. Educational but cinematic in composition. FILL THE ENTIRE FRAME edge to edge, no letterbox, no pillarbox, no black bars. Any on-image label, badge, sign, or diagram text must sit fully inside a 10 percent margin from every edge. Never place text flush with the top, bottom, or sides of the frame. Not photorealistic, not 3D, not anime, not painterly, not generic stock imagery. Accent this title with a graphite, paper-white, and signal-orange palette; keep the same clean flat 2D construction. Not photorealistic, not a photograph, not cinematic photography, not 3D, not Pixar, not anime, not manga, not watercolor, not oil painting, not hyper-detailed, not a superhero comic, not photomontage, not DSLR, not realistic skin texture. NO swastika, NO Nazi flag, NO SS runes, NO armbands, NO camps, NO gore, NO celebrity photoreal faces. No readable paragraphs of body copy, no watermarks, no captions overlaid on the frame unless the scene names a short on-screen label. Not a 3D corporate animation, not a stock-photo slideshow, not a Bloomberg terminal wall of numbers, not a photoreal product shot. CHARACTER shopper: adult with short dark side-parted hair, simple oval cartoon face, navy crewneck sweater over a cream collar, flat 2D vector, NOT photoreal CHARACTER clerk: younger adult, pulled-back brown hair, simple cartoon face, apricot apron over a white shirt, flat 2D vector, NOT photoreal CHARACTER banker: older adult, short steel-grey hair, two-circle cartoon glasses, charcoal jacket, pale shirt, no tie, flat 2D vector, NOT photoreal"

STILLS: list[tuple[str, str, str]] = [
    ("medium shot", "hero", "CHECKOUT Shopper taps a plain white card on a black terminal. No logos."),
    ("wide shot", "empty", "FOUR_DESKS Four simple desks. A thin teal line hops them. No logos."),
    ("wide shot", "empty", "NETWORK_ROOM THE_AUTHORIZATION_PULSE A coin-sized teal authorization pulse, glowing, large in frame, high contrast, the same simple orb every time travels a dark aisle of teal slabs."),
    ("close-up", "empty", "CHECKOUT Tiny teal sliver next to a fat orange bar on a blank receipt. No logos."),
    ("wide shot", "empty", "WORLD_MAP A gold arc over a navy map. No country names."),
    ("medium shot", "hero", "BANK_OFFICE Banker holds a plain white card. No logos."),
    ("title card", "empty", "End card. Dark navy field. No people. Type added in assemble."),

]


def prompt_for(who: str, scene: str) -> str:
    extra = "STRICTLY NO people, NO faces, NO hands." if who == "empty" else (
        "Only named characters. Same cartoon construction every time."
    )
    return f"{STYLE} {extra} SCENE: {scene}"
