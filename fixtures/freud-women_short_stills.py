"""Auto-generated stills for freud-women. Do not hardcode a person here;
character looks come from the project bible frozen below."""

from __future__ import annotations

PROP_BUDGET = {'THE_FOLDER': 6}
SET_TOKENS = ['CONSULT_ROOM', 'FOLDER_DESK', 'VIENNA_STAIR', 'EMPTY_CHAIR', 'PRINT_SHOP', 'MAP_TABLE', 'BERLIN_STUDY', 'LECTURE_HALL', 'TRAIN_PLATFORM', 'MUSEUM_ROOM', 'LONDON_DESK']

STYLE = "Simple flat 2D historical educational animation in the established What They Really Think visual identity. Clean vector-like digital illustration, simplified human anatomy, simple facial features (simple eyes, simple nose, simple mouth), clear recognizable silhouettes, flat colors, muted historical palette, minimal gradients, restrained shading, softly illustrated simplified background, uncluttered composition, expressive but restrained poses, consistent recurring character design, clean educational animation aesthetic. FILL THE ENTIRE FRAME edge to edge, no letterbox, no pillarbox, no black bars. Any on-image label, badge, sign, or diagram text must sit fully inside a 10 percent margin from every edge. Never place text flush with the top, bottom, or sides of the frame. Accent this title with a moss-green and parchment palette; keep the same flat 2D construction. Not photorealistic, not a photograph, not cinematic photography, not 3D, not Pixar, not anime, not manga, not watercolor, not oil painting, not hyper-detailed, not a superhero comic, not photomontage, not DSLR, not realistic skin texture. NO swastika, NO Nazi flag, NO SS runes, NO armbands, NO camps, NO gore, NO celebrity photoreal faces. No readable paragraphs of body copy, no watermarks, no captions overlaid on the frame unless the scene names a short on-screen label. older man, high balding forehead, dark hair at the sides, neat short grey-white beard, round wire glasses, three-piece brown wool suit, watch chain, simple cartoon eyes. Same cartoon person every time. Flat 2D vector, NOT photoreal, NOT a celebrity photograph. young woman, late teens, dark hair in a low knot, high-collar cream 1900 dress and wool coat, simple cartoon face, modest historical clothing. Not a caricature. Flat 2D, NOT photoreal. woman in her 40s, short waved brown hair, round glasses, dark jacket, simple cartoon face. Flat 2D, NOT photoreal. woman, dark waved hair, pale 1920s dress, simple cartoon face, no crown. Flat 2D, NOT photoreal. younger woman, dark bob, severe grey jacket, simple cartoon face. Flat 2D, NOT photoreal. generic early-1900s extras, simple cartoon faces. Flat 2D, NOT photoreal."

STILLS: list[tuple[str, str, str]] = [
    ("wide shot", "empty", "EMPTY_CHAIR Wooden consulting chair pulled back, cushion dented, no person."),
    ("object close-up", "empty", "FOLDER_DESK THE_FOLDER a huge thick cream case folder tied with a bright red ribbon, big as a serving board, high contrast on a dark desk, filling the middle of the frame, same obvious folder every time, not a faint paper, not a tiny notebook."),
    ("wide shot", "other", "VIENNA_STAIR Young woman, late teens, dark hair in a low knot, cream wool coat leaving a peg, no face."),
    ("medium shot", "hero", "CONSULT_ROOM Balding man, neat grey-white beard, round wire glasses, brown three-piece suit, simple cartoon eyes, at the empty couch."),
    ("symbolic image", "empty", "MAP_TABLE Cream map with an unlabeled dark oval hole, lamp through the gap, no country names."),
    ("title card", "empty", "End card. Dark navy field. No people. Type added in assemble."),

]


def prompt_for(who: str, scene: str) -> str:
    extra = "STRICTLY NO people, NO faces, NO hands." if who == "empty" else (
        "Only named characters. Same cartoon construction every time."
    )
    return f"{STYLE} {extra} SCENE: {scene}"
