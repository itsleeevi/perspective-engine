"""Stills for hitler_americans.json v4 — one per narration chunk.

v4 is a continuous perspective story, not a numbered lecture. Visual job is
the same: SAME cowboy paperback, SAME rain-window office, SAME hero, SAME
American everyman. Match-cut the book. Callback the opening drawer.

No Nazi flags, no swastikas, no armbands, no camps, no war-gore.
HERO is a stylized 1930s German official (graphic-novel, CLEAN-SHAVEN — image
models block the historical mustache). Do not name a historical person in
the prompt.
"""

from __future__ import annotations

# Enforced by scripts/lint_storyboard.py. The shipped v4 storyboard VIOLATES
# these budgets (THE BOOK is in 47/77 scenes) — that is why the cut reads as
# a screensaver. The next rewrite of this title must pass the linter.
PROP_BUDGET = {"THE BOOK": 6}
SET_TOKENS = ["THE OFFICE"]

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

# (shot_type, who, scene) — 1:1 with split_beat_into_chunks at NARRATION_WPM=175
STILLS: list[tuple[str, str, str]] = [
    ("wide shot", "empty", "1945 Berlin: a splintered office door kicked inward, rain, war maps on a steel desk, chairs kicked over. They came looking for maps. No people. No book yet."),
    ("top-down flatlay", "empty", "MATCH CUT closer: war maps, arrows, pencils, a brass lamp still on. The mess of a lost army. No people. No book yet."),
    ("top-down flatlay", "empty", "MATCH CUT: the SAME maps, now with THE BOOK lying on top, soft cover, painted horse, warm lamp. They found a cowboy novel. No people."),
    ("extreme close-up", "empty", "THE BOOK fill-frame: soft brown cover, painted rearing horse, worn German paperback. Soft cover. No people."),
    ("medium shot", "empty", "THE BOOK sitting on the war desk as if it had been waiting, lamp, rain on the blotter. No people."),
    ("extreme close-up", "empty", "A handless still: THE BOOK half in an open wooden drawer. Sit with it. No people."),
    ("medium shot", "hero", f"{OFFICE} HERO at the open drawer, THE BOOK in his hands like a secret. A child's western in a war room."),
    ("wide shot", "empty", "Empty New York sidewalk at dawn, closed diner window, wet street. He had never been. No people."),
    ("wide shot", "empty", "Silent car factory floor, heat shimmer, no workers. A floor that comes up through your shoes. No people."),
    ("symbolic graphic", "empty", "A paper map of America folded like a file folder, no country-scale life. America was not a country. No people."),
    ("extreme close-up", "empty", "Paper, ink, a dead radio speaker, THE BOOK beside them. A smell of paper, a voice on a speaker. No people."),
    ("over-the-shoulder", "crowd", "A German boy from behind, blanket, flashlight, THE BOOK open to a painted West. A picture he drew when he was small. NO HERO face."),
    ("medium shot", "hero", f"{OFFICE} HERO looking into camera, THE BOOK on the desk. So what did he actually think Americans were?"),
    ("wide shot", "empty", "Empty school hallway, flag at the far end, no people. Not a speech they teach in school."),
    ("wide shot", "american", "AMERICAN as a painted cowboy extra, frozen mid-gesture, THE BOOK in the foreground. A cartoon that cannot surprise you. NO HERO."),
    ("medium shot", "hero", f"{OFFICE} HERO closing THE BOOK as if the story is already finished. He decides the country is done."),
    ("symbolic graphic", "empty", "THE BOOK standing like a last page on a globe turned to the Atlantic. He will bet the world on it. No people."),
    ("over-the-shoulder", "crowd", "Same boy from behind, THE BOOK huge in his lap, not an American street. He did not read America. NO HERO face."),
    ("extreme close-up", "empty", "THE BOOK's painted West: horses, honor, empty land that never existed. No people."),
    ("wide shot", "empty", "Empty painted prairie, a hero-shaped shadow that keeps its word, no ticket booth. No people."),
    ("medium shot", "hero", f"{OFFICE} HERO holding THE BOOK to his chest like a religion. Rain on the window."),
    ("medium shot", "hero", f"MATCH CUT time jump: {OFFICE} Adult HERO, same charcoal suit, THE BOOK still open. Forty years later the boy is gone."),
    ("medium shot", "hero", f"{OFFICE} Watch him. Same man. Same suit. Same rain on the window. THE BOOK on the desk."),
    ("wide shot", "hero", f"{OFFICE} HERO telling a campfire story, tiny generic flag pin, United States as folklore. THE BOOK in his hand."),
    ("extreme close-up", "empty", "A small flag pin on charcoal wool, THE BOOK out of focus behind it. No people."),
    ("medium shot", "hero", f"{OFFICE} HERO running a country from THE BOOK, maps shoved aside. A grown man on a novel."),
    ("wide shot", "crowd", "AMERICAN and extras as tiny figures on THE BOOK's cover, like movie extras. Simple. Loud. Late. NO HERO."),
    ("wide shot", "american", "AMERICAN useless in a real paneled room, then useful on a painted horse. He liked them better that way. NO HERO."),
    ("symbolic graphic", "empty", "A toy cowboy next to a copied paper silhouette of the same cowboy. Easy to hate, easy to copy. No people."),
    ("medium shot", "hero", f"{OFFICE} HERO needing both: contempt and a copy, THE BOOK under his palm."),
    ("wide shot", "hero", "Dark newsreel booth off the SAME office: HERO watching skyscrapers and chorus lines, treating movies like reconnaissance. THE BOOK on the seat."),
    ("wide shot", "empty", "A generic ape-on-a-tower silhouette on a movie screen, jazz lights smeared. No people. No celebrity likeness."),
    ("top-down flatlay", "empty", "Gum, a football, a movie-kiss still, a spy notepad. He wrote entertainment down as intelligence. No people."),
    ("medium shot", "hero", "HERO watching a tiny American city diorama through thick zoo glass. THE BOOK in his pocket."),
    ("extreme close-up", "empty", "Zoo glass, city lights smeared, fingerprints. Sure the animals cannot get out. No people."),
    ("wide shot", "crowd", "Movie cowboy arriving late, audience clapping, AMERICAN clapping too. America was late. America was soft. NO HERO."),
    ("top-down flatlay", "empty", "A film strip laid over a Detroit car brochure, THE BOOK beside them. Film logic. He never smelled the plant. No people."),
    ("wide shot", "crowd", "Detroit assembly line, cars like a river, anonymous workers from behind. Not a people. A river of cars. NO HERO."),
    ("symbolic graphic", "empty", "America drawn as a method diagram, people erased into arrows. Methods can be copied. No people."),
    ("medium shot", "hero", f"{OFFICE} HERO doing small math on factory photos, THE BOOK pushed aside. The math made them small."),
    ("medium shot", "hero", f"{OFFICE} HERO at the glowing radio, leather flight helmet on the table, THE BOOK still there. Stay out. Stay home. No flyer face."),
    ("extreme close-up", "empty", "Radio grille, a stamped FILE folder, THE BOOK under the paper. He filed that voice as the real United States. No people."),
    ("wide shot", "empty", "Fireside armchair, radio glow, empty room, no portrait. Filed as a glitch. No people."),
    ("symbolic graphic", "empty", "A country torn down the middle, one half stamped fake. You do not beat a country that way. No people."),
    ("wide shot", "hero", f"{OFFICE} HERO drawing the Atlantic as a castle moat on a map, THE BOOK holding the paper down."),
    ("wide shot", "empty", "A theater: Europe on the stage, America as the darkened audience. No people."),
    ("wide shot", "empty", "The darkened theater, empty seats, a stage no one climbs. Audiences do not climb on. No people."),
    ("aerial", "empty", "1936 stadium from above, two teams walking in, no faces readable. The country he had never visited. No people visible."),
    ("wide shot", "crowd", "A track team in a tunnel, not cowboys. Anonymous Black sprinter from behind, gold light, NOT a celebrity portrait."),
    ("wide shot", "crowd", "Stadium crowd as a wave of sound, THE BOOK tiny on a box-seat railing. The novel cannot hold this. NO HERO face."),
    ("medium shot", "hero", "HERO in the stadium box, camera-smile that does not reach his eyes, THE BOOK on his knee. The western broke. He heard it."),
    ("medium shot", "hero", f"Back in {OFFICE} HERO putting THE BOOK back in the SAME drawer. He heard the truth and filed it."),
    ("medium shot", "hero", f"{OFFICE} HERO clutching THE BOOK with both hands, refusing the crack."),
    ("medium shot", "hero", f"{OFFICE} HERO choosing THE BOOK again, same rain, same suit. He always chose the book."),
    ("symbolic graphic", "empty", "An old picture of a painted West taped over a living stadium. He will bet the world on the old one. No people."),
    ("top-down flatlay", "empty", "A December calendar page, Pacific water stain, THE BOOK closed beside it. December is coming. No people."),
    ("extreme close-up", "empty", "THE BOOK's last page beside a dead radio, Pacific water on the blotter. December does not care what he filed. No people."),
    ("top-down flatlay", "empty", "Pacific water, smoke, a generic flag edge, THE BOOK closed. A Sunday not in the paperback. No people."),
    ("wide shot", "american", "AMERICAN launching off the sofa, gum, radio glow. The country standing up. NO HERO."),
    ("wide shot", "empty", "A newsreel projector throwing a blur too slow for the room. The newsreel could not keep up. No people."),
    ("wide shot", "soldier", "Troop ships, SOLDIER on a wet dock. America entering the story. THE BOOK is not here. NO HERO."),
    ("medium shot", "hero", f"{OFFICE} HERO stamping a form as if cancelling a subscription, THE BOOK under his elbow. Four days later."),
    ("wide shot", "empty", "An American street he had never seen, empty dawn, no people."),
    ("top-down flatlay", "empty", "Ape still, car brochure, radio, THE BOOK. That is all he had seen. No people."),
    ("wide shot", "soldier", "SOLDIER and GIs climbing onto a theater stage from the audience. The audience climbed on. NO HERO."),
    ("wide shot", "soldier", "A million ordinary men, SOLDIER in front, gum, factory skyline behind them. Not cowboys."),
    ("wide shot", "soldier", "SOLDIER filling the movie-ending frame; THE BOOK lies in the aisle like a dead extra. They arrived as the ending."),
    ("extreme close-up", "empty", "THE BOOK in the aisle, open to a blank last page. The paperback had no chapter for that. No people."),
    ("top-down flatlay", "empty", "CALLBACK: the SAME drawer as the first maps, THE BOOK returned, pages soft, spine broken. Last shot. No people."),
    ("wide shot", "empty", "Unused passport, ocean window, empty chair. He died having never seen it. No people."),
    ("top-down flatlay", "empty", "THE BOOK on the war desk, too small for a war. Not a small error. No people."),
    ("symbolic graphic", "empty", "THE BOOK as a coffin-shaped shadow on a world map. The whole war hiding in a story. No people."),
    ("medium shot", "hero", f"{OFFICE} HERO in unglamorous shadow, THE BOOK on the desk. If you want a monster, you already have one."),
    ("medium shot", "hero", "HERO looking at a fake movie-America on a screen with the wrong kind of love. THE BOOK in his hands."),
    ("wide shot", "soldier", "Real SOLDIER and AMERICAN walking toward camera as a painted cowboy dissolves. The real one would not stay fake."),
    ("medium shot", "hero", f"{OFFICE} HERO reaching as if the country belonged to him, THE BOOK falling from his hand."),
    ("aerial", "empty", "A living country from above, lights, rivers, not a last page. He thought they were his. They weren't. No people visible."),
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
