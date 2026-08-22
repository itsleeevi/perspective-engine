"""Stills for hitler_americans.json v2 — one per chunk.

Story spine: a cowboy paperback, not a roast folder. Third-person narrator.
No Nazi flags, no swastikas, no armbands, no camps, no war-gore.
HERO is a stylized 1930s German official (graphic-novel, not a photo, NO mustache —
image models block the historical mustache).
Movie coverage: hero is NOT in every frame. No celebrity likenesses (no Ford face,
no flyer face, no sprinter portrait, no White House portrait).
"""

from __future__ import annotations

HERO = (
    "HERO (same man every time): stylized graphic-novel 1930s European official, "
    "dark side-parted hair, CLEAN-SHAVEN, NO mustache, pale intense face, cold pale "
    "eyes, ALWAYS the same charcoal three-piece suit and plain dark tie, NO medals, "
    "NO armbands, NO symbols, painterly, NOT a photograph, NOT photoreal."
)

AMERICAN = (
    "AMERICAN (same man every time): late-thirties everyman, short brown hair, weary "
    "small dark eyes, slightly oversized round cartoon head that still sits on his neck, "
    "average build, clothes change with the scene, not a celebrity."
)

SOLDIER = (
    "SOLDIER (same man): 1940s American GI, early 20s, short dark hair, tired honest face, "
    "khaki kit, gum in his pocket, not a celebrity, not the cartoon everyman, not HERO."
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
    + NO_NAZI + HERO + " " + AMERICAN + " " + SOLDIER
)

STYLE_EMPTY = (
    "Award-shot 16:9 anamorphic movie still FILLING THE ENTIRE FRAME edge to edge, "
    "no letterbox, no pillarbox, no black bars. Rich color, film grain, motivated lighting, "
    "warm amber and cold graphite, painterly graphic-novel. STRICTLY NO people, NO faces, "
    "NO hands, NO human silhouettes. No readable text, letters, numbers, logos, watermarks, captions. "
    + NO_NAZI
)

# (shot_type, who, scene) — must stay 1:1 with split_beat_into_chunks of the fixture.
STILLS: list[tuple[str, str, str]] = [
    ("wide shot", "empty", "Ruined 1945 office, maps unrolled across a steel desk, rain light, chairs kicked over. They expected maps. No people."),
    ("top-down flatlay", "empty", "A cheap German cowboy paperback lying on top of the war maps, soft cover, painted horse, no readable title. No people."),
    ("medium shot", "crowd", "A German boy seen strictly from behind, dark hair, hiding under a wool blanket with a flashlight and that cowboy book. Not identifiable. NO HERO face."),
    ("wide shot", "hero", "HERO at a rain window, a globe turned to the Atlantic, never packing a suitcase. He never set foot there."),
    ("medium shot", "hero", "HERO looks into camera, the cowboy book in his hands. Stay. The ending is worse than the joke."),
    ("extreme close-up", "empty", "An unused steamer trunk, empty hangers, a blank destination tag. He never went. No people."),
    ("symbolic graphic", "empty", "A hole punched clean through a painted map of the United States, light pouring through. Every opinion built on that hole. No people."),
    ("wide shot", "empty", "Triptych of empty places: a wet New York sidewalk at dawn, a closed diner, a silent factory floor. No people."),
    ("top-down flatlay", "empty", "A mail sack spilled: magazines, a cowboy paperback, a film reel, stamps. America arrived by mail. No people."),
    ("over-the-shoulder", "crowd", "Over the boy's shoulder: the cowboy book open, a painted West, a German attic lamp. He did not read America. NO HERO."),
    ("extreme close-up", "empty", "An illustrated West that never existed: fake mesas, a painted sunset on cheap paper. No people."),
    ("wide shot", "empty", "Empty painted prairie, horses without riders, honor as a vast vacant land. No people."),
    ("symbolic graphic", "empty", "Two illustrated figures on a book page keeping their word: a cowboy and a warrior, painterly, not celebrities, no faces large. No people."),
    ("medium shot", "hero", "HERO clutching the same paperback at his adult desk like a religion, lamp, rain."),
    ("medium shot", "hero", "HERO older, forty years later, the boy gone, the same book still open. Watch him."),
    ("wide shot", "hero", "HERO telling a campfire story, a tiny flag pin on the table, the United States as folklore."),
    ("extreme close-up", "empty", "The cowboy book's spine against his temple, as if that is how a brain is wired. No faces. No people."),
    ("wide shot", "hero", "HERO in a dark newsreel booth, skyscrapers like movie sets blasting the screen. Hollywood sent the sequel free."),
    ("wide shot", "crowd", "Movie-palace screen: chorus line and a generic giant ape silhouette on an art-deco tower, AMERICAN in the front row. NO HERO. Not a branded character."),
    ("medium shot", "hero", "HERO watching a tiny American city diorama through zoo glass, sure he is safe."),
    ("extreme close-up", "empty", "Thick zoo glass, city lights smeared on the far side, fingerprints. Animals cannot get out. No people."),
    ("wide shot", "american", "A jazz club that will not sit still, AMERICAN dancing in the aisle, brass, smoke. NO HERO."),
    ("dutch angle", "american", "Ballpark bleachers, AMERICAN chewing gum like a species, football pads stacked like a religion. Daylight. NO HERO."),
    ("top-down flatlay", "empty", "A spy folder beside a movie ticket and a gum wrapper. Intelligence vs entertainment. No people."),
    ("medium shot", "hero", "HERO leaning into camera, the dangerous trick in his eyes."),
    ("wide shot", "hero", "HERO in a cinema with binoculars, treating the movie as a scouting report."),
    ("wide shot", "empty", "Movie screen: a cowboy arriving late under a huge clock. America was late. No people."),
    ("wide shot", "crowd", "Audience clapping, AMERICAN clapping too, the clapping read as softness. NO HERO."),
    ("wide shot", "american", "Ballroom, a girl kissing a stranger because the band is playing, AMERICAN in the doorway. NO HERO."),
    ("symbolic graphic", "empty", "A film strip laid over a war map, sprocket holes as strategy. War on film logic. No people."),
    ("wide shot", "empty", "A torn western poster with a Detroit factory photograph showing underneath. Not in a western. No people."),
    ("wide shot", "crowd", "Detroit assembly line as a miracle, sparks, a factory saint of machines, no celebrity faces, workers anonymous from behind."),
    ("aerial", "empty", "Cars pouring off a line like a river of steel, God's-eye, no people visible."),
    ("extreme close-up", "empty", "A hollow car chassis, beautiful and empty, a machine with no soul. No people."),
    ("symbolic graphic", "empty", "A precision gear beside a single candle. Machines are easy. Souls are not. No people."),
    ("top-down flatlay", "empty", "Factory brochures and quotes arranged like a saint's shrine. Collected like relics. No people."),
    ("wide shot", "empty", "A factory he had never smelled: glossy brochure in the foreground, real steam and rust far away. No people."),
    ("symbolic graphic", "empty", "The United States drawn as a method diagram, people erased into arrows and boxes. No people."),
    ("medium shot", "hero", "HERO doing the math on factory photos, liking the numbers, the lie already in the pencil."),
    ("medium shot", "hero", "HERO at a glowing radio, a leather flight helmet on the table, preferring this American. No flyer face."),
    ("extreme close-up", "empty", "Radio grille, a closed door, the ocean in the window. Stay out. Stay home. No people."),
    ("medium shot", "hero", "HERO filing a radio transcript as if it is the real United States."),
    ("wide shot", "empty", "Fireside armchair, radio glow, empty White House-like room, no portrait, no famous face. Filed as a glitch. No people."),
    ("symbolic graphic", "empty", "A painted map of the country ripped in half, one half stamped real, one half discarded. No people."),
    ("aerial", "empty", "1936 stadium from above, two teams walking in, flags too distant to read. He had never visited. No people visible."),
    ("wide shot", "crowd", "A track team in a tunnel, not cowboys, a nation as a team. Generic athletes, no celebrity likeness."),
    ("wide shot", "crowd", "Anonymous Black sprinter from behind, gold light, stadium roar, NOT a celebrity portrait, crowd as a sound."),
    ("medium shot", "hero", "HERO in the box, a camera-smile that does not reach his eyes, the western cracking."),
    ("extreme close-up", "empty", "A cowboy illustration cracked down the middle like glass. He refused to hear it. No people."),
    ("wide shot", "empty", "Not a battlefield: an office chair, a lamp, a book, no trenches. No people."),
    ("medium shot", "hero", "HERO protecting the paperback with both hands, a man protecting a story."),
    ("medium shot", "hero", "HERO small in a huge chair, reading the cowboy book, he is only the reader."),
    ("wide shot", "crowd", "A living crowd that does not care about his ending, AMERICAN among them, HERO a speck in a box."),
    ("medium shot", "hero", "HERO choosing the book on his lap over the window full of crowd. Every time."),
    ("symbolic graphic", "empty", "The Atlantic painted as a castle moat, Europe a chessboard, water black and final. No people."),
    ("wide shot", "empty", "A theater: Europe on the stage, America as the darkened audience. Audiences do not climb on. No people."),
    ("extreme close-up", "empty", "A giant padlock on a door made of ocean. The whole foreign policy. No people."),
    ("wide shot", "empty", "Toy-small ships on a vast sea, a navy underestimated on purpose. No people."),
    ("top-down flatlay", "empty", "A December calendar, Pacific water in a dish, the cowboy paperback closed beside it. No people."),
    ("extreme close-up", "empty", "Smoke and a generic flag edge, no symbols, no people."),
    ("wide shot", "american", "AMERICAN launching off a sofa, gum, a newsreel blur, the country standing up too fast. NO HERO."),
    ("medium shot", "hero", "HERO still in the European office. He did not go to America."),
    ("wide shot", "soldier", "Troop ships and SOLDIER on a wet dock, America entering the story without asking. NO HERO."),
    ("medium shot", "hero", "HERO stamping a form as if cancelling a subscription, four days later, war as paperwork."),
    ("wide shot", "empty", "An American street he had never seen: brick, fire escape, morning. No people."),
    ("top-down flatlay", "empty", "The ape-on-a-building still beside a car brochure. That is what he had seen. No people."),
    ("medium shot", "hero", "HERO at the radio, saying yes, them too."),
    ("two-person shot", "hero", "Generals with steel ship models; HERO holding a movie script instead. He understood plot."),
    ("wide shot", "crowd", "A mixed, noisy, rich street parade, AMERICAN in it, jazz and gold, the plot where they lose. NO HERO."),
    ("tracking", "empty", "A film reel unwinding beside a convoy of ships already moving. Plot is a drug. No people."),
    ("extreme close-up", "empty", "The novel's last page, blank, no more pages. No people."),
    ("wide shot", "soldier", "SOLDIER and other GIs climbing onto a theater stage from the audience. Not as a cowboy. NO HERO."),
    ("wide shot", "soldier", "A million ordinary men, SOLDIER in front, gum, a factory skyline behind them."),
    ("top-down flatlay", "empty", "A call sheet of extras versus a blank last chapter. He had written them as extras. No people."),
    ("wide shot", "soldier", "SOLDIER filling the movie-ending frame, the extras arriving as the ending. NO HERO."),
    ("top-down flatlay", "empty", "A stack of substitutes: western, zoo glass, car brochure, radio. Not a speech. No people."),
    ("top-down flatlay", "empty", "Boy's western, zoo glass, factory-saint brochure, radio hero helmet. The whole stack. No people."),
    ("wide shot", "empty", "A movie theater whose aisle is an ocean moat, the film still playing, nobody leaving. No people."),
    ("symbolic graphic", "empty", "A globe on a poker table, the bet of a world. No people."),
    ("top-down flatlay", "empty", "The last object in the drawer: the same cowboy book, pages soft. No people."),
    ("extreme close-up", "empty", "Spine broken from being believed too long, paper fibers. No people."),
    ("wide shot", "empty", "Unused passport, ocean window, empty chair. He died having never seen it. No people."),
    ("top-down flatlay", "empty", "The paperback sitting on the war desk, the whole war hiding in it. No people."),
    ("medium shot", "hero", "HERO in unglamorous shadow. If you want a monster, you already have one."),
    ("symbolic graphic", "empty", "The mechanism laid out: book, movie reel, radio, a stamped yes. No people."),
    ("medium shot", "hero", "HERO looking at a fake movie-America on a screen with the wrong kind of love."),
    ("wide shot", "soldier", "Real SOLDIER and AMERICAN walking toward camera as a painted cowboy dissolves. The real one would not stay fake."),
    ("medium shot", "american", "AMERICAN holding the cowboy book out to the viewer. Send this. The book always ends."),
    ("aerial", "empty", "A living country from above, lights, rivers, not a last page. The country does not. No people visible."),
]


def prompt_for(who: str, scene: str) -> str:
    if who == "empty":
        return f"{STYLE_EMPTY} SCENE: {scene}"
    extras = {
        "hero": "Only HERO on camera unless the scene names someone else in bokeh. Same charcoal three-piece every time. CLEAN-SHAVEN, NO mustache. NO symbols.",
        "american": "AMERICAN is the lead. HERO is absent unless the scene names him.",
        "both": "HERO and AMERICAN both visible, locked faces. CLEAN-SHAVEN HERO, NO mustache.",
        "soldier": "SOLDIER is the lead. HERO only if named as a speck. Cartoon AMERICAN is absent unless named.",
        "crowd": "Generic extras, not celebrities. Recurring leads only if named. NO politician faces. NO symbols. NO HERO unless named.",
    }
    return f"{STYLE_PEOPLE} {extras.get(who, '')} SCENE: {scene}"
