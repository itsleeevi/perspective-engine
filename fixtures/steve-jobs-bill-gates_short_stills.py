"""Auto-generated stills for steve-jobs-bill-gates. Do not hardcode a person here;
character looks come from the project bible frozen below."""

from __future__ import annotations

PROP_BUDGET = {'THE_MAC': 6}
SET_TOKENS = ['BANDLEY_ROOM', 'XEROX_PARC', 'CUPERTINO_LAB', 'WINDOWS_OFFICE', 'NEXT_LOFT', 'MACWORLD_HALL', 'PALO_ALTO_HOME', 'GARAGE_BENCH', 'CITY_NEWS']

STYLE = "Simple flat 2D historical educational animation in the established What They Really Think visual identity. Clean vector-like digital illustration, simplified human anatomy, simple facial features (simple eyes, simple nose, simple mouth), clear recognizable silhouettes, flat colors, muted historical palette, minimal gradients, restrained shading, softly illustrated simplified background, uncluttered composition, expressive but restrained poses, consistent recurring character design, clean educational animation aesthetic. FILL THE ENTIRE FRAME edge to edge, no letterbox, no pillarbox, no black bars. Any on-image label, badge, sign, or diagram text must sit fully inside a 10 percent margin from every edge. Never place text flush with the top, bottom, or sides of the frame. Not photorealistic, not a photograph, not cinematic photography, not 3D, not Pixar, not anime, not manga, not watercolor, not oil painting, not hyper-detailed, not a superhero comic, not photomontage, not DSLR, not realistic skin texture. NO swastika, NO Nazi flag, NO SS runes, NO armbands, NO camps, NO gore, NO celebrity photoreal faces. No readable paragraphs of body copy, no watermarks, no captions overlaid on the frame unless the scene names a short on-screen label. CHARACTER subject_young: thin young man, late 20s, dark brown hair with a slight wave, clean-shaven, simple round cartoon eyes, simple nose, simple mouth, pale mock-turtleneck or white shirt, blue jeans, sometimes a dark jacket. Same cartoon person every time. Flat 2D vector, NOT photoreal, NOT a celebrity likeness. CHARACTER subject_adult: thinner older man, 40s to 50s, receding dark hair going grey at the temples, clean-shaven, small round glasses, simple cartoon eyes, black turtleneck, jeans. Same cartoon person as subject_young, older. Flat 2D vector, NOT photoreal, NOT a celebrity likeness. CHARACTER rival_young: young man, oversized round glasses, floppy light-brown hair, simple cartoon face, awkward navy sweater or ill-fitting suit, slightly hunched. Flat 2D vector, NOT photoreal, NOT a celebrity likeness. CHARACTER rival_adult: middle-aged man, receding brown hair, larger round glasses, simple cartoon face, pale blue shirt or sweater. Same cartoon person as rival_young, older. Flat 2D vector, NOT photoreal, NOT a celebrity likeness. CHARACTER mac_staff: generic early-eighties engineers, curly or straight hair, casual shirts, simple cartoon faces, sitting along a conference table. Same construction as the other characters. Flat 2D vector, NOT photoreal."

STILLS: list[tuple[str, str, str]] = [
    ("establishing shot", "empty", "BANDLEY_ROOM Beige conference room, long table, empty chairs, ugly tiles."),
    ("two-person shot", "other", "BANDLEY_ROOM Young thin dark-haired man leans in shouting; young glasses man stands still."),
    ("symbolic image", "empty", "XEROX_PARC House and television icon, night, no readable address."),
    ("medium shot", "hero", "NEXT_LOFT Older turtleneck man at a camera, taste-complaint face."),
    ("wide shot", "other", "MACWORLD_HALL Giant glasses-wearing face on a wall screen over a tiny stage."),
    ("object close-up", "empty", "CUPERTINO_LAB THE_MAC beige compact beside a cheap grey window-grid, no type."),
    ("title card", "empty", "End card. Dark navy field. No people. Type added in assemble."),

]


def prompt_for(who: str, scene: str) -> str:
    extra = "STRICTLY NO people, NO faces, NO hands." if who == "empty" else (
        "Only named characters. Same cartoon construction every time."
    )
    return f"{STYLE} {extra} SCENE: {scene}"
