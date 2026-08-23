"""Auto-generated stills for sam-altman-the-future-of-work. Do not hardcode a person here;
character looks come from the project bible frozen below."""

from __future__ import annotations

PROP_BUDGET = {'THE_CHECK': 6}
SET_TOKENS = ['INBOX_NIGHT', 'ESSAY_DESK', 'LEGAL_OFFICE', 'CLINIC', 'FACTORY', 'HOUSE_SITE', 'AI_LAB', 'SENATE_ROOM', 'EMPTY_FLOOR', 'MAILBOX_STREET', 'ORB_BOOTH', 'CITY_NIGHT']

STYLE = "Simple flat 2D historical educational animation in the established What They Really Think visual identity. Clean vector-like digital illustration, simplified human anatomy, simple facial features (simple eyes, simple nose, simple mouth), clear recognizable silhouettes, flat colors, muted historical palette, minimal gradients, restrained shading, softly illustrated simplified background, uncluttered composition, expressive but restrained poses, consistent recurring character design, clean educational animation aesthetic. FILL THE ENTIRE FRAME edge to edge, no letterbox, no pillarbox, no black bars. Any on-image label, badge, sign, or diagram text must sit fully inside a 10 percent margin from every edge. Never place text flush with the top, bottom, or sides of the frame. Not photorealistic, not a photograph, not cinematic photography, not 3D, not Pixar, not anime, not manga, not watercolor, not oil painting, not hyper-detailed, not a superhero comic, not photomontage, not DSLR, not realistic skin texture. NO swastika, NO Nazi flag, NO SS runes, NO armbands, NO camps, NO gore, NO celebrity photoreal faces. No readable paragraphs of body copy, no watermarks, no captions overlaid on the frame unless the scene names a short on-screen label. CHARACTER subject: slim man, 30s to 40s, short curly-wavy brown hair, clean-shaven or light stubble, simple cartoon eyes, plain grey t-shirt or dark hoodie. Same cartoon person every time. Flat 2D vector, NOT photoreal, NOT a celebrity likeness. CHARACTER senator: older man, grey hair, dark suit, simple cartoon face, sitting behind a wood nameplate with no readable name. Flat 2D vector, NOT photoreal. CHARACTER clerk: generic office worker, simple cartoon face, button shirt, at a laptop. Flat 2D vector, NOT photoreal. CHARACTER coder: young adult, simple cartoon face, hoodie, headphones around the neck, at a glowing screen. Flat 2D vector, NOT photoreal."

STILLS: list[tuple[str, str, str]] = [
    ("document close-up", "empty", "ESSAY_DESK A spare desk, one monitor, a nearly blank white page, daylight, no logos."),
    ("object close-up", "empty", "FACTORY A wage envelope on a bench, the ink fading to blank."),
    ("object close-up", "empty", "MAILBOX_STREET Coins and a folded paper check dropping into a wooden box, no numbers."),
    ("object close-up", "empty", "INBOX_NIGHT A laptop screen filling itself with grey bars, no letters."),
    ("medium shot", "hero", "MAILBOX_STREET Slim curly-haired man in a grey t-shirt holds a folded paper check, not smiling."),
    ("title card", "empty", "End card. Dark navy field. No people. Type added in assemble."),

]


def prompt_for(who: str, scene: str) -> str:
    extra = "STRICTLY NO people, NO faces, NO hands." if who == "empty" else (
        "Only named characters. Same cartoon construction every time."
    )
    return f"{STYLE} {extra} SCENE: {scene}"
