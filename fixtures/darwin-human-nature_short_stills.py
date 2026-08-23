"""Auto-generated stills for darwin-human-nature. Do not hardcode a person here;
character looks come from the project bible frozen below."""

from __future__ import annotations

PROP_BUDGET = {'THE_FORK': 6}
SET_TOKENS = ['NOTEBOOK_DESK', 'BEAGLE_DECK', 'FUEGO_SHORE', 'BRAZIL_STREET', 'DOWN_STUDY', 'PRINT_SHOP', 'WALLACE_DESK', 'NURSERY', 'DOG_HEARTH', 'LECTURE_HALL', 'CAMBRIDGE_CASE', 'BUTTON_TABLE', 'FORK_TABLE']

STYLE = "Simple flat 2D historical educational animation in the established What They Really Think visual identity. Clean vector-like digital illustration, simplified human anatomy, simple facial features (simple eyes, simple nose, simple mouth), clear recognizable silhouettes, flat colors, muted historical palette, minimal gradients, restrained shading, softly illustrated simplified background, uncluttered composition, expressive but restrained poses, consistent recurring character design, clean educational animation aesthetic. FILL THE ENTIRE FRAME edge to edge, no letterbox, no pillarbox, no black bars. Any on-image label, badge, sign, or diagram text must sit fully inside a 10 percent margin from every edge. Never place text flush with the top, bottom, or sides of the frame. Not photorealistic, not a photograph, not cinematic photography, not 3D, not Pixar, not anime, not manga, not watercolor, not oil painting, not hyper-detailed, not a superhero comic, not photomontage, not DSLR, not realistic skin texture. NO swastika, NO Nazi flag, NO SS runes, NO armbands, NO camps, NO gore, NO celebrity photoreal faces. No readable paragraphs of body copy, no watermarks, no captions overlaid on the frame unless the scene names a short on-screen label. older man, 50s-60s, high balding forehead, long full grey-white beard, heavy brow, simple cartoon eyes, black Victorian coat over a cream shirt. Same cartoon person every time. Flat 2D vector, NOT photoreal, NOT a celebrity photograph. young man, late teens, dark brown skin, short black hair, dignified simple cartoon face, dark wool coat over a pale shirt. Not a caricature. Flat 2D, NOT photoreal. naval officer, 30s, dark blue coat, clean chin, simple cartoon face. Flat 2D, NOT photoreal. lean bearded man, thinner face, brown coat, simple cartoon eyes, not the grey-beard hero. Flat 2D, NOT photoreal. generic Victorian extras, simple cartoon faces. Flat 2D, NOT photoreal."

STILLS: list[tuple[str, str, str]] = [
    ("document close-up", "empty", "NOTEBOOK_DESK Open brown pocket notebook, two short pencil marks, no readable paragraph."),
    ("symbolic image", "empty", "NOTEBOOK_DESK THE_FORK a huge pale Y-shaped birch twig, thick as a wrist, bright cream wood against a dark table, filling the middle of the frame, high contrast, same obvious branching stick every time, no writing, not a faint sketch, not a tiny doodle."),
    ("medium shot", "hero", "DOWN_STUDY Balding grey-beard man in a black coat over a cream shirt, heavy brow, simple cartoon eyes, at a window."),
    ("close-up", "other", "BUTTON_TABLE Young man, dark brown skin, short black hair, dignified simple cartoon face, holding a huge pale pearl button."),
    ("wide shot", "empty", "DOG_HEARTH A hearth rug and a sleeping hound, fire glow."),
    ("wide shot", "empty", "LECTURE_HALL Empty wood benches, one oil lamp, a chalkboard with a simple Y fork and no letters."),
    ("title card", "empty", "End card. Dark navy field. No people. Type added in assemble."),

]


def prompt_for(who: str, scene: str) -> str:
    extra = "STRICTLY NO people, NO faces, NO hands." if who == "empty" else (
        "Only named characters. Same cartoon construction every time."
    )
    return f"{STYLE} {extra} SCENE: {scene}"
