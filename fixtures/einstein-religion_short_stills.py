"""Auto-generated stills for einstein-religion. Do not hardcode a person here;
character looks come from the project bible frozen below."""

from __future__ import annotations

PROP_BUDGET = {'THE_LETTER': 6}
SET_TOKENS = ['CABLE_OFFICE', 'BERLIN_ROOM', 'NEWSSTAND', 'BOY_ROOM', 'BLACKBOARD_HALL', 'LIBRARY_HALL', 'PRINCETON_STUDY', 'STREET_FRAME']

STYLE = "Simple flat 2D historical educational animation in the established What They Really Think visual identity. Clean vector-like digital illustration, simplified human anatomy, simple facial features (simple eyes, simple nose, simple mouth), clear recognizable silhouettes, flat colors, muted historical palette, minimal gradients, restrained shading, softly illustrated simplified background, uncluttered composition, expressive but restrained poses, consistent recurring character design, clean educational animation aesthetic. FILL THE ENTIRE FRAME edge to edge, no letterbox, no pillarbox, no black bars. Not photorealistic, not a photograph, not cinematic photography, not 3D, not Pixar, not anime, not manga, not watercolor, not oil painting, not hyper-detailed, not a superhero comic, not photomontage, not DSLR, not realistic skin texture. NO swastika, NO Nazi flag, NO SS runes, NO armbands, NO camps, NO gore, NO celebrity photoreal faces. No readable paragraphs of body copy, no watermarks, no captions overlaid on the frame unless the scene names a short on-screen label. CHARACTER subject_adult: older European man, late 40s to 70s, wild grey-white hair standing out in a halo, thick drooping grey moustache, simple round cartoon eyes, simple nose, simple mouth, medium build, rumpled brown-grey wool suit, cream shirt, sometimes a loose dark tie. Same cartoon person every time. Flat 2D vector, NOT photoreal, NOT a celebrity likeness. CHARACTER subject_boy: same person as a boy about twelve, dark brown hair already a little wild, no moustache, simple round cartoon eyes, school jacket and collar, slightly smaller frame. Clearly the same cartoon person younger. Flat 2D vector, NOT photoreal. CHARACTER cable_rabbi: middle-aged man, neat dark hair, round glasses, dark city suit, holding a telegram form. Simple cartoon face. Flat 2D vector, NOT photoreal. CHARACTER physicist_friend: middle-aged European man, thinning dark hair, round glasses, dark academic suit, holding a letter. Simple cartoon face. Flat 2D vector, NOT photoreal."

STILLS: list[tuple[str, str, str]] = [
    ("over-the-shoulder", "hero", "PRINCETON_STUDY THE_LETTER: older wild-haired man writes by hand at a wooden night desk, fountain pen, window."),
    ("document", "empty", "PRINCETON_STUDY THE_LETTER close-up, one short line, no paragraphs."),
    ("medium shot", "other", "CABLE_OFFICE Man with round glasses at a telegraph counter, waiting, telegram in hand."),
    ("symbolic image", "empty", "BLACKBOARD_HALL Orbit circles on a blackboard, no listening face in the sky."),
    ("close-up", "hero", "PRINCETON_STUDY Same cartoon older man, calm face, wild hair, thick moustache, not kneeling."),
    ("establishing shot", "empty", "PRINCETON_STUDY Empty study, lamp on, unfinished papers. Vertical 9:16 subject large in upper two thirds."),

]


def prompt_for(who: str, scene: str) -> str:
    extra = "STRICTLY NO people, NO faces, NO hands." if who == "empty" else (
        "Only named characters. Same cartoon construction every time."
    )
    return f"{STYLE} {extra} SCENE: {scene}"
