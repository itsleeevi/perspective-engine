"""Auto-generated stills for jeff-bezos-elon-musk. Do not hardcode a person here;
character looks come from the project bible frozen below."""

from __future__ import annotations

PROP_BUDGET = {'THE_TORTOISE': 6}
SET_TOKENS = ['X_PHONE', 'CREST_WALL', 'WEST_TEXAS', 'PAD_39', 'COURTROOM', 'HANGAR', 'BARGE', 'PARIS_STAGE', 'FACTORY', 'AISLE', 'NIGHT_DESK', 'HATCH_SHOP', 'BOOM_PAD', 'MOON_TABLE']

STYLE = "Simple flat 2D historical educational animation in the established What They Really Think visual identity. Clean vector-like digital illustration, simplified human anatomy, simple facial features (simple eyes, simple nose, simple mouth), clear recognizable silhouettes, flat colors, muted historical palette, minimal gradients, restrained shading, softly illustrated simplified background, uncluttered composition, expressive but restrained poses, consistent recurring character design, clean educational animation aesthetic. FILL THE ENTIRE FRAME edge to edge, no letterbox, no pillarbox, no black bars. Any on-image label, badge, sign, or diagram text must sit fully inside a 10 percent margin from every edge. Never place text flush with the top, bottom, or sides of the frame. Not photorealistic, not a photograph, not cinematic photography, not 3D, not Pixar, not anime, not manga, not watercolor, not oil painting, not hyper-detailed, not a superhero comic, not photomontage, not DSLR, not realistic skin texture. NO swastika, NO Nazi flag, NO SS runes, NO armbands, NO camps, NO gore, NO celebrity photoreal faces. No readable paragraphs of body copy, no watermarks, no captions overlaid on the frame unless the scene names a short on-screen label. fit man, early 60s, fully shaved bald scalp, pale high forehead, square cartoon face, wide mouth, clean-shaven, navy flight jacket over a light blue open-collar shirt. Same cartoon person every time. Flat 2D vector, NOT photoreal, NOT a celebrity photograph. tall slim man, 50s, receding brown hair swept back from a high forehead, long oval face, prominent chin, thin mouth, simple cartoon eyes set close, plain black t-shirt, slightly stooped tall walk. Same cartoon person every time. Flat 2D vector, NOT photoreal, NOT a celebrity photograph. adult in an orange vest and hard hat, simple cartoon face. Flat 2D, NOT photoreal."

STILLS: list[tuple[str, str, str]] = [
    ("object close-up", "empty", "X_PHONE A dark phone showing one grey tortoise photo, no letters."),
    ("symbolic image", "empty", "CREST_WALL THE_TORTOISE a huge dark-green tortoise statue with a bright gold shell, as big as a suitcase, sitting dead center in the frame, high contrast, no writing, not a pin, not a stamp, not tiny."),
    ("medium shot", "hero", "CREST_WALL Bald navy-jacket man looking at THE_TORTOISE a huge dark-green tortoise statue with a bright gold shell, as big as a suitcase, sitting dead center in the frame, high contrast, no writing, not a pin, not a stamp, not tiny."),
    ("medium shot", "other", "HANGAR Tall receding-hair black-t-shirt man beside a white rocket body."),
    ("wide shot", "empty", "COURTROOM Wood dais and a thick folder with a blank red bar."),
    ("wide shot", "empty", "BOOM_PAD Scorched concrete and a bent rail, white smoke."),
    ("title card", "empty", "End card. Dark navy field. No people. Type added in assemble."),

]


def prompt_for(who: str, scene: str) -> str:
    extra = "STRICTLY NO people, NO faces, NO hands." if who == "empty" else (
        "Only named characters. Same cartoon construction every time."
    )
    return f"{STYLE} {extra} SCENE: {scene}"
