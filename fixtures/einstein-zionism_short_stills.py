"""Auto-generated stills for einstein-zionism. Do not hardcode a person here;
character looks come from the project bible frozen below."""

from __future__ import annotations

PROP_BUDGET = {'THE_ENVELOPE': 6}
SET_TOKENS = ['PRINCETON_STUDY', 'OCEAN_LINER', 'BANQUET_HALL', 'JERUSALEM_HILL', 'HOTEL_BALLROOM', 'NEWSSTAND', 'EMBASSY_DESK', 'EMPTY_DAIS']

STYLE = "Simple flat 2D historical educational animation in the established What They Really Think visual identity. Clean vector-like digital illustration, simplified human anatomy, simple facial features (simple eyes, simple nose, simple mouth), clear recognizable silhouettes, flat colors, muted historical palette, minimal gradients, restrained shading, softly illustrated simplified background, uncluttered composition, expressive but restrained poses, consistent recurring character design, clean educational animation aesthetic. FILL THE ENTIRE FRAME edge to edge, no letterbox, no pillarbox, no black bars. Any on-image label, badge, sign, or diagram text must sit fully inside a 10 percent margin from every edge. Never place text flush with the top, bottom, or sides of the frame. Not photorealistic, not a photograph, not cinematic photography, not 3D, not Pixar, not anime, not manga, not watercolor, not oil painting, not hyper-detailed, not a superhero comic, not photomontage, not DSLR, not realistic skin texture. NO swastika, NO Nazi flag, NO SS runes, NO armbands, NO camps, NO gore, NO celebrity photoreal faces. No readable paragraphs of body copy, no watermarks, no captions overlaid on the frame unless the scene names a short on-screen label. CHARACTER subject_adult: older European man, late 40s to 70s, wild grey-white hair standing out in a halo, thick drooping grey moustache, simple round cartoon eyes, simple nose, simple mouth, medium build, rumpled brown-grey wool suit, cream shirt, sometimes a loose dark tie. Same cartoon person every time. Flat 2D vector, NOT photoreal, NOT a celebrity likeness. CHARACTER chemist_organizer: middle-aged European man, receding dark hair, small neat goatee, round simple cartoon face, dark 1920s suit, high collar, shorter than the wild-haired man. Flat 2D vector, NOT photoreal. CHARACTER young_diplomat: slim man in his thirties, dark neat hair, simple round glasses, dark diplomatic suit, thin tie, often holding an envelope. Simple cartoon face. Flat 2D vector, NOT photoreal."

STILLS: list[tuple[str, str, str]] = [
    ("newspaper", "empty", "NEWSSTAND Vertical 9:16 frame, evening papers on a city stand, huge question-mark headline block, no readable paragraphs."),
    ("medium shot", "hero", "PRINCETON_STUDY Vertical 9:16 frame, older wild-haired man shaking his head at a wooden desk, rumpled brown-grey suit."),
    ("close-up", "hero", "PRINCETON_STUDY Vertical 9:16 frame, older wild-haired man at the study window, looking out, quiet face."),
    ("establishing", "empty", "OCEAN_LINER Vertical 9:16 frame, 1920s steamship bow and cream funnels, grey sea, no people."),
    ("crowd", "crowd", "BANQUET_HALL Vertical 9:16 frame, round banquet tables and simplified guests raising glasses, no readable menus."),
    ("establishing", "empty", "EMPTY_DAIS Vertical 9:16 frame, empty ceremonial wooden chair under a simple arch, no emblems, no people."),
    ("object close-up", "empty", "PRINCETON_STUDY Vertical 9:16 frame, THE_ENVELOPE lying sealed on a wooden desk, window light, no people."),
    ("establishing", "empty", "JERUSALEM_HILL Vertical 9:16 frame, pale unfinished university buildings on a hill, wide sky, no people."),
    ("wide shot", "empty", "EMPTY_DAIS Vertical 9:16 frame, unused ceremonial chair in shadow, a folded blank cloth, no people."),
    ("medium shot", "hero", "PRINCETON_STUDY Vertical 9:16 frame, older wild-haired man looking past camera, study window behind him."),

]


def prompt_for(who: str, scene: str) -> str:
    extra = "STRICTLY NO people, NO faces, NO hands." if who == "empty" else (
        "Only named characters. Same cartoon construction every time."
    )
    return f"{STYLE} {extra} SCENE: {scene}"
