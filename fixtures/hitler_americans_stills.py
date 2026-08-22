"""Stills for hitler_americans.json v3 — one per chunk.

Visual continuity is the job: SAME cowboy paperback, SAME rain-window office,
SAME hero, SAME American everyman. Hollywood match-cuts, not a random slideshow.

No Nazi flags, no swastikas, no armbands, no camps, no war-gore.
HERO is a stylized 1930s German official (graphic-novel, CLEAN-SHAVEN — image
models block the historical mustache).
"""

from __future__ import annotations

HERO = (
    "HERO (same man every time, do not redesign): stylized graphic-novel 1930s "
    "European official, dark side-parted hair combed flat, CLEAN-SHAVEN, NO mustache, "
    "pale intense face, cold pale eyes, ALWAYS the same charcoal three-piece suit and "
    "plain dark tie, NO medals, NO armbands, NO symbols, painterly, NOT a photograph."
)

AMERICAN = (
    "AMERICAN (same man every time, do not redesign): late-thirties everyman, short "
    "brown hair, weary small dark eyes, slightly oversized round cartoon head that "
    "still sits on his neck, average build, clothes change with the scene, not a celebrity."
)

SOLDIER = (
    "SOLDIER (same man): 1940s American GI, early 20s, short dark hair, tired honest face, "
    "khaki kit, gum, not a celebrity, not HERO, not the cartoon everyman."
)

BOOK = (
    "THE BOOK (same prop every time): a cheap German cowboy paperback, soft brown cover, "
    "painted rearing horse, worn spine. It must look like the SAME physical object whenever it appears."
)

OFFICE = (
    "THE OFFICE (same set): 1940s rain-window night office, steel desk, brass lamp, "
    "the cowboy paperback on the desk. Return to this room whenever HERO is working."
)

NO_NAZI = (
    "NO swastika, NO Nazi flag, NO SS runes, NO armbands, NO camps, NO Holocaust imagery, "
    "NO gore, NO celebrity politician faces, NO photoreal famous people. "
)

STYLE_PEOPLE = (
    "Award-shot 16:9 anamorphic movie still FILLING THE ENTIRE FRAME edge to edge, "
    "no letterbox, no pillarbox, no black bars. Rich color, film grain, motivated lighting, "
    "warm amber and cold graphite, painterly graphic-novel, drop-dead cinematic composition. "
    "No readable text, letters, numbers, logos, watermarks, captions. "
    + NO_NAZI + HERO + " " + AMERICAN + " " + SOLDIER + " " + BOOK + " " + OFFICE
)

STYLE_EMPTY = (
    "Award-shot 16:9 anamorphic movie still FILLING THE ENTIRE FRAME edge to edge, "
    "no letterbox, no pillarbox, no black bars. Rich color, film grain, motivated lighting, "
    "warm amber and cold graphite, painterly graphic-novel. STRICTLY NO people, NO faces, "
    "NO hands, NO human silhouettes. No readable text, letters, numbers, logos, watermarks, captions. "
    + NO_NAZI + BOOK + " "
)

# (shot_type, who, scene) — 1:1 with split_beat_into_chunks at NARRATION_WPM=205
STILLS: list[tuple[str, str, str]] = [
    ("wide shot", "empty", "1945 ruined office, war maps unrolled on a steel desk, rain light, chairs kicked over. They expected maps. No people. No book yet."),
    ("top-down flatlay", "empty", "MATCH CUT: the SAME maps, now with THE BOOK lying on top, soft cover, painted horse. A boy's book on a war desk. No people."),
    ("medium shot", "hero", f"{OFFICE} HERO looks into camera, five fingers raised, THE BOOK in his other hand. Stay. I am going to count the fakes."),
    ("wide shot", "soldier", "End-of-movie energy: SOLDIER and GIs stepping through a cinema screen into rain, THE BOOK lying forgotten in the aisle. The real country walks in."),
    ("wide shot", "empty", "Empty New York sidewalk at dawn, closed diner window, no people. The hole. He never went."),
    ("wide shot", "empty", "Silent factory floor, then a dead radio speaker. He never smelled America. No people."),
    ("medium shot", "hero", f"{OFFICE} HERO over a globe turned to the Atlantic, THE BOOK closed. Say it again. He never went."),
    ("over-the-shoulder", "crowd", "FAKE ONE. German boy from behind, blanket, flashlight, THE BOOK open to a painted West. He did not read America. NO HERO face."),
    ("extreme close-up", "empty", "THE BOOK's painted West: horses, honor, empty land that never existed. No people."),
    ("wide shot", "empty", "Empty painted prairie, a hero-shaped shadow that keeps its word. No people."),
    ("medium shot", "hero", f"MATCH CUT time jump: the boy is gone. {OFFICE} Adult HERO, same charcoal suit, THE BOOK still open. Forty years later."),
    ("medium shot", "hero", f"{OFFICE} Watch him. Same man. Same suit. Same rain on the window. THE BOOK on the desk."),
    ("wide shot", "hero", f"{OFFICE} HERO telling a campfire story, tiny flag pin, United States as folklore. THE BOOK in his hand."),
    ("top-down flatlay", "empty", "FAKE ONE still open: THE BOOK on the steel desk, lamp, rain on the blotter. No people."),
    ("wide shot", "hero", f"FAKE TWO. Dark newsreel booth off the SAME office: HERO watching skyscrapers and a generic ape-on-a-tower. THE BOOK on the seat beside him."),
    ("medium shot", "hero", "HERO watching a tiny American city diorama through thick zoo glass, sure he is safe. THE BOOK in his pocket."),
    ("extreme close-up", "empty", "Zoo glass, city lights smeared, fingerprints. Animals cannot get out. No people."),
    ("wide shot", "american", "AMERICAN in a jazz-and-football night: gum, a movie kiss in the background. The country cannot sit still. NO HERO."),
    ("top-down flatlay", "empty", "Spy folder beside a movie ticket and THE BOOK. Intelligence vs entertainment. No people."),
    ("wide shot", "hero", "HERO in the cinema with binoculars, movie as a scouting report. THE BOOK on the next seat."),
    ("wide shot", "crowd", "Movie cowboy arriving late, audience clapping, AMERICAN clapping too. America was late. America was soft. NO HERO."),
    ("symbolic graphic", "empty", "MATCH CUT: zoo glass over THE BOOK's cover. Film logic and the paperback are the same lie. No people."),
    ("symbolic graphic", "empty", "Two costumes of one lie: a film strip and THE BOOK, same horse painted on both. No people."),
    ("wide shot", "crowd", "FAKE THREE. Detroit assembly line, cars like a river, anonymous workers from behind. Not a cowboy. A factory."),
    ("top-down flatlay", "empty", "Factory brochure arranged like a saint's shrine beside THE BOOK. He had the brochure. No people."),
    ("symbolic graphic", "empty", "America drawn as a method diagram, people erased into arrows. No people."),
    ("medium shot", "hero", f"{OFFICE} HERO doing the math on factory photos, THE BOOK pushed aside, the lie in the pencil."),
    ("medium shot", "hero", f"FAKE FOUR. {OFFICE} HERO at the glowing radio, leather flight helmet on the table, THE BOOK still there. No flyer face."),
    ("extreme close-up", "empty", "Radio grille, closed door, ocean in the window. Stay out. Stay home. No people."),
    ("medium shot", "hero", f"{OFFICE} HERO filing a radio transcript as if it is the real United States. THE BOOK under the paper."),
    ("wide shot", "empty", "Fireside armchair, radio glow, empty room, no portrait. Filed as a glitch. No people."),
    ("top-down flatlay", "empty", "Four objects in a row: THE BOOK, a film reel, a car brochure, a radio. Four fakes so far. No people."),
    ("top-down flatlay", "empty", "The same four objects plus an empty space for one more. Book. Movie. Factory. Radio. One more. No people."),
    ("symbolic graphic", "empty", "FAKE FIVE. The Atlantic painted as a castle moat, Europe a chessboard, THE BOOK tiny on the European shore. No people."),
    ("wide shot", "empty", "A theater: Europe on the stage, America as the darkened audience. Audiences do not climb on. No people."),
    ("extreme close-up", "empty", "A giant padlock on a door made of ocean. The whole foreign policy. No people."),
    ("top-down flatlay", "empty", "Five objects: THE BOOK, film, brochure, radio, a black ribbon of ocean. None of them were the country. No people."),
    ("aerial", "empty", "THE CRACK. 1936 stadium from above, two teams walking in. He had never visited. No people visible."),
    ("wide shot", "crowd", "A track team in a tunnel, not cowboys. Anonymous Black sprinter from behind, gold light, NOT a celebrity portrait."),
    ("medium shot", "hero", "HERO in the stadium box, camera-smile that does not reach his eyes, THE BOOK on his knee. The crowd made a sound."),
    ("medium shot", "hero", f"Back in {OFFICE} HERO clutching THE BOOK with both hands, refusing the crack. He chose the book. Every time."),
    ("top-down flatlay", "empty", "December calendar, Pacific water, THE BOOK closed beside it. A Sunday not in the paperback. No people."),
    ("extreme close-up", "empty", "Smoke and a generic flag edge, no symbols. No people."),
    ("wide shot", "american", "AMERICAN launching off the sofa, gum, newsreel blur. The country standing up. NO HERO."),
    ("wide shot", "soldier", "Troop ships, SOLDIER on a wet dock. America entering the story. THE BOOK is not here. NO HERO."),
    ("medium shot", "hero", f"{OFFICE} HERO stamping a form as if cancelling a subscription, THE BOOK under his elbow. Four days later."),
    ("wide shot", "empty", "An American street he had never seen, then a flash of the ape-still. He had seen the ape. No people."),
    ("top-down flatlay", "empty", "Ape still, car brochure, radio, THE BOOK. That is all he had seen. No people."),
    ("tracking", "empty", "Film reel unwinding beside a convoy already moving. Plot is a drug. No people."),
    ("wide shot", "soldier", "FAKE FIVE DIES. SOLDIER and GIs climbing onto a theater stage from the audience. Not as a cowboy. NO HERO."),
    ("wide shot", "soldier", "A million ordinary men, SOLDIER in front, gum, factory skyline behind them."),
    ("wide shot", "soldier", "SOLDIER filling the movie-ending frame; THE BOOK lies in the aisle like a dead extra. They arrived as the ending."),
    ("top-down flatlay", "empty", "Five substitutes in a stack: western, zoo glass, car saint, radio, moat. Not a speech. No people."),
    ("top-down flatlay", "empty", "The same five objects, closer. A boy's western. A zoo glass. A car saint. A radio hero. A moat. No people."),
    ("wide shot", "empty", "A movie theater whose aisle is an ocean, the film still playing, nobody leaving. He bet the world. No people."),
    ("top-down flatlay", "empty", "CALLBACK: the SAME drawer as the first maps, THE BOOK returned, pages soft, spine broken. Last shot. No people."),
    ("wide shot", "empty", "Unused passport, ocean window, empty chair. He died having never seen it. No people."),
    ("top-down flatlay", "empty", "THE BOOK on the war desk. The whole war hiding in a paperback. No people."),
    ("medium shot", "hero", f"{OFFICE} HERO in unglamorous shadow, THE BOOK on the desk. If you want a monster, you already have one."),
    ("medium shot", "hero", "HERO looking at a fake movie-America on a screen with the wrong kind of love. THE BOOK in his hands."),
    ("wide shot", "soldier", "Real SOLDIER and AMERICAN walking toward camera as a painted cowboy dissolves. The real one would not stay fake."),
    ("aerial", "empty", "A living country from above, lights, rivers, not a last page. The book always ends. The country does not. No people visible."),
]


def prompt_for(who: str, scene: str) -> str:
    if who == "empty":
        return f"{STYLE_EMPTY} SCENE: {scene}"
    extras = {
        "hero": "Only HERO on camera unless the scene names someone else in bokeh. Same charcoal three-piece every time. CLEAN-SHAVEN, NO mustache. THE BOOK visible if the scene names it. NO symbols.",
        "american": "AMERICAN is the lead. HERO is absent unless the scene names him.",
        "soldier": "SOLDIER is the lead. HERO only if named as a speck. Cartoon AMERICAN is absent unless named.",
        "crowd": "Generic extras, not celebrities. Recurring leads only if named. NO politician faces. NO symbols. NO HERO unless named.",
    }
    return f"{STYLE_PEOPLE} {extras.get(who, '')} SCENE: {scene}"
