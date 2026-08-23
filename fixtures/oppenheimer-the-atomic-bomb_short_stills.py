"""Auto-generated stills for oppenheimer-the-atomic-bomb. Do not hardcode a person here;
character looks come from the project bible frozen below."""

from __future__ import annotations

PROP_BUDGET = {'THE_GADGET': 6}
SET_TOKENS = ['THE_MESA', 'THE_LAB', 'THE_DESERT', 'THE_RALLY', 'THE_WHITE_HOUSE', 'THE_HEARING_ROOM', 'THE_STUDY', 'THE_FRAME', 'THE_SKY', 'THE_CITY']

STYLE = "Simple flat 2D historical educational animation in the established What They Really Think visual identity. Clean vector-like digital illustration, simplified human anatomy, simple facial features (simple eyes, simple nose, simple mouth), clear recognizable silhouettes, flat colors, muted historical palette, minimal gradients, restrained shading, softly illustrated simplified background, uncluttered composition, expressive but restrained poses, consistent recurring character design, clean educational animation aesthetic. FILL THE ENTIRE FRAME edge to edge, no letterbox, no pillarbox, no black bars. Not photorealistic, not a photograph, not cinematic photography, not 3D, not Pixar, not anime, not manga, not watercolor, not oil painting, not hyper-detailed, not a superhero comic, not photomontage, not DSLR, not realistic skin texture. NO swastika, NO Nazi flag, NO SS runes, NO armbands, NO camps, NO gore, NO celebrity photoreal faces. No readable paragraphs of body copy, no watermarks, no captions overlaid on the frame unless the scene names a short on-screen label. CHARACTER director (same cartoon person every time, do not redesign): a very tall, gaunt, thin man in his forties, long angular face, sharp cheekbones, pale skin, large pale blue eyes, short cropped dark brown hair, clean-shaven; wears a loose brown three-piece suit and a wide flat-brimmed pale porkpie hat, often holding a thin smoking pipe; calm, intense, slightly haunted expression; flat 2D vector, simple facial features, muted palette, NOT photoreal, NOT a celebrity likeness. CHARACTER general (same cartoon person every time): a heavyset older army officer, round jowly face, thin mustache, receding hair, khaki military dress uniform with brass buttons and ribbons; stern, impatient; flat 2D vector, simple facial features, muted palette, NOT photoreal. CHARACTER president (same cartoon person every time): a trim older man, round wire-frame glasses, neat side-parted grey hair, plain dark double-breasted suit and bow tie; composed, cold; flat 2D vector, simple facial features, muted palette, NOT photoreal."

STILLS: list[tuple[str, str, str]] = [
    ("symbolic image", "empty", "THE_FRAME A vertical flat graphic of a wall calendar turning to the month of August 1945, muted palette, no people, no readable paragraphs."),
    ("medium shot", "hero", "THE_RALLY Vertical frame: the tall thin man in a pale porkpie hat on a low stage clasps both hands over his head like a victorious boxer, a cheering crowd below."),
    ("wide shot", "crowd", "THE_RALLY Vertical frame: rows of simplified staff cheer with raised arms under bunting, the thin man raised above them on the stage."),
    ("close-up", "hero", "THE_RALLY Vertical close-up of the thin man's face faltering in the middle of the cheer, doubt creeping into his eyes."),
    ("two-person shot", "other", "THE_WHITE_HOUSE Vertical frame: the thin man stands before a composed bespectacled older man seated at a large desk in a formal office."),
    ("close-up", "hero", "THE_WHITE_HOUSE Vertical close-up of the thin man's downcast face and his open hands, a faint red stain implied on the palms."),
    ("medium shot", "other", "THE_WHITE_HOUSE Vertical frame: the bespectacled older man waves a cold, dismissive hand toward a door."),
    ("symbolic image", "empty", "THE_SKY Vertical frame: a small blue globe sealed in a cracked glass dome, fragile in a muted void, no people."),
    ("close-up", "hero", "THE_STUDY Vertical close-up of the man's haunted face in dusk light, looking to one side, a question in his eyes."),
    ("symbolic image", "empty", "THE_FRAME Vertical end-card graphic: a small play-icon beside a faint mushroom-cloud silhouette, muted, no readable paragraphs, no people."),

]


def prompt_for(who: str, scene: str) -> str:
    extra = "STRICTLY NO people, NO faces, NO hands." if who == "empty" else (
        "Only named characters. Same cartoon construction every time."
    )
    return f"{STYLE} {extra} SCENE: {scene}"
