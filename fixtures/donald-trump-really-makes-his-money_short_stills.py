"""Auto-generated stills for donald-trump-really-makes-his-money. Do not hardcode a person here;
character looks come from the project bible frozen below."""

from __future__ import annotations

PROP_BUDGET = {'THE_BLANK_GOLD_HOTEL_NAMEPLATE': 6}
SET_TOKENS = ['MARBLE_OFFICE', 'NAMEPLATE_SHOP', 'TOWER_LOBBY', 'NIGHT_CRANE', 'BRICK_STOOP', 'CASINO_DARK', 'TV_BOARDROOM', 'GOLF_FAIRWAY', 'CLUB_DESK', 'TICKER_HALL', 'ETHICS_DESK', 'COURT_STEPS', 'JET_CABIN', 'GOLD_CORRIDOR', 'MAP_TABLE', 'RECORDING_BOOTH']

STYLE = "Clean flat 2D business documentary illustration in the established Behind The Business channel identity. Modern vector-like shapes, simple readable characters, simplified products and environments, crisp diagrams, subtle depth, limited shading, clean high-contrast palette, uncluttered compositions, clear information hierarchy, visually intuitive financial flows and business systems, consistent recurring locations and company elements. Educational but cinematic in composition. FILL THE ENTIRE FRAME edge to edge, no letterbox, no pillarbox, no black bars. Any on-image label, badge, sign, or diagram text must sit fully inside a 10 percent margin from every edge. Never place text flush with the top, bottom, or sides of the frame. Not photorealistic, not 3D, not anime, not painterly, not generic stock imagery. Accent this title with a graphite, paper-white, and signal-orange palette; keep the same clean flat 2D construction. Not photorealistic, not a photograph, not cinematic photography, not 3D, not Pixar, not anime, not manga, not watercolor, not oil painting, not hyper-detailed, not a superhero comic, not photomontage, not DSLR, not realistic skin texture. NO swastika, NO Nazi flag, NO SS runes, NO armbands, NO camps, NO gore, NO celebrity photoreal faces. No readable paragraphs of body copy, no watermarks, no captions overlaid on the frame unless the scene names a short on-screen label. Not a 3D corporate animation, not a stock-photo slideshow, not a Bloomberg terminal wall of numbers, not a photoreal product shot. Same cartoon tycoon every time, do not redesign. Swept gold-blond hair piled high in a distinctive comb-over mound. Orange-tan oval face. Small squinting eyes. Tiny mouth. Oversized boxy navy-blue suit with huge shoulders. Extra-long bright red necktie hanging far below the belt. Blank gold hotel nameplate on a lanyard, no letters. Simple flat 2D cartoon construction, two-dot eyes, no skin texture, no photo. Adult developer in a yellow hard hat and orange safety vest. Simple flat face. No logos. No readable type. Older landlord in a long gray overcoat holding a heavy key ring. Thin gray hair. Simple flat face. No logos. No readable type. Young adult in a plain gray hoodie holding a blank magazine. Simple flat face. No logos. No readable type. Adult club member in a plain cream polo holding a blank gold card with no letters. Simple flat face. No logos. No flags."

STILLS: list[tuple[str, str, str]] = [
    ("wide shot", "hero", "NIGHT_CRANE Cartoon tycoon slams a fat unlabeled magazine onto marble beside a thin invoice, papers exploding, extra-long red necktie flying. Low sun cuts a long red-necktie shadow across the floor. Accent: upper-left gold lamp, warm amber light, wide empty margin on the right. No logos. No readable type."),
    ("medium shot", "hero", "MARBLE_OFFICE Cartoon tycoon holds the fat magazine in one fist and the thin invoice in the other like a referee, navy suit huge in frame. Tiny eyes squint at the thin invoice. Accent: lower-right blue window, warm amber light, wide empty margin on the left. No logos. No readable type. THE_BLANK_GOLD_HOTEL_NAMEPLATE the same oversized blank gold hotel nameplate with no letters sits large in frame."),
    ("close-up", "crowd", "NIGHT_CRANE A developer in an orange vest shaking on a thin invoice, unfinished tower behind, no logos. Developers crowd a night site under a crane. Accent: center marble gleam, warm amber light, open ceiling space. No logos. No readable type."),
    ("over-the-shoulder", "empty", "ETHICS_DESK Certified stamp on a form that still hides cash, cool light, no figures. A chandelier over empty casino felt. Accent: left crane cable, warm amber light, open floor space. No logos. No readable type."),
    ("low angle", "empty", "TICKER_HALL Huge unlabeled ticker wall, short sales bar beside tall ownership block, no letters, no numbers, no people. Night rain on glass, no silhouettes. Accent: right empty chair, warm amber light, deep foreground object. No logos. No readable type."),
    ("high angle", "hero", "MARBLE_OFFICE Cartoon tycoon walks down a gold corridor dragging the fat binder like a suitcase, thin invoice in his breast pocket. Wind flips the fat magazine pages. Accent: ceiling chandelier, warm amber light, far miniature skyline. No logos. No readable type."),
    ("title card", "empty", "End card. Dark navy field. No people. Type added in assemble."),

]


def prompt_for(who: str, scene: str) -> str:
    extra = "STRICTLY NO people, NO faces, NO hands." if who == "empty" else (
        "Only named characters. Same cartoon construction every time."
    )
    return f"{STYLE} {extra} SCENE: {scene}"
