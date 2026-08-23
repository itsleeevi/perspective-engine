"""Auto-generated stills for elon-musk-ai. Do not hardcode a person here;
character looks come from the project bible frozen below."""

from __future__ import annotations

PROP_BUDGET = {'THE_CIRCLE': 6}
SET_TOKENS = ['MIT_STAGE', 'WHITE_LAB', 'NIGHT_DESK', 'COURTROOM', 'MEMPHIS_HALL', 'CAR_LINE', 'ROCKET_BAY', 'CITY_DUSK', 'CHALK_FLOOR', 'SERVER_CAGE', 'HANGAR_DOOR', 'KITCHEN_TV']

STYLE = "Simple flat 2D historical educational animation in the established What They Really Think visual identity. Clean vector-like digital illustration, simplified human anatomy, simple facial features (simple eyes, simple nose, simple mouth), clear recognizable silhouettes, flat colors, muted historical palette, minimal gradients, restrained shading, softly illustrated simplified background, uncluttered composition, expressive but restrained poses, consistent recurring character design, clean educational animation aesthetic. FILL THE ENTIRE FRAME edge to edge, no letterbox, no pillarbox, no black bars. Any on-image label, badge, sign, or diagram text must sit fully inside a 10 percent margin from every edge. Never place text flush with the top, bottom, or sides of the frame. Not photorealistic, not a photograph, not cinematic photography, not 3D, not Pixar, not anime, not manga, not watercolor, not oil painting, not hyper-detailed, not a superhero comic, not photomontage, not DSLR, not realistic skin texture. NO swastika, NO Nazi flag, NO SS runes, NO armbands, NO camps, NO gore, NO celebrity photoreal faces. No readable paragraphs of body copy, no watermarks, no captions overlaid on the frame unless the scene names a short on-screen label. tall slim man, 50s, receding brown hair swept back from a high forehead, long oval face, prominent chin, thin mouth, simple cartoon eyes set close, plain black t-shirt, slightly stooped tall walk. Same cartoon person every time. Flat 2D vector, NOT photoreal, NOT a celebrity photograph. older man, grey hair, glasses, dark suit, simple cartoon face. Flat 2D, NOT photoreal. young adult, hoodie, simple cartoon face. Flat 2D, NOT photoreal."

STILLS: list[tuple[str, str, str]] = [
    ("medium shot", "hero", "MIT_STAGE Tall receding-hair black-t-shirt man on a small stage, not smiling."),
    ("symbolic image", "empty", "CHALK_FLOOR THE_CIRCLE a huge thick bright white chalk ring, as thick as a rope, glowing on a black floor, filling the middle of the frame, high contrast, no writing, not faint, not brown, not a stain."),
    ("wide shot", "hero", "CHALK_FLOOR Tall receding-hair black-t-shirt man stepping inside THE_CIRCLE a huge thick bright white chalk ring, as thick as a rope, glowing on a black floor, filling the middle of the frame, high contrast, no writing, not faint, not brown, not a stain."),
    ("wide shot", "crowd", "ROCKET_BAY Engineers in a ring around a dark terminal."),
    ("wide shot", "empty", "MEMPHIS_HALL A warehouse of cabinets lighting one by one, no logos."),
    ("medium shot", "hero", "MEMPHIS_HALL Tall receding-hair black-t-shirt man among blinking racks."),
    ("title card", "empty", "End card. Dark navy field. No people. Type added in assemble."),

]


def prompt_for(who: str, scene: str) -> str:
    extra = "STRICTLY NO people, NO faces, NO hands." if who == "empty" else (
        "Only named characters. Same cartoon construction every time."
    )
    return f"{STYLE} {extra} SCENE: {scene}"
