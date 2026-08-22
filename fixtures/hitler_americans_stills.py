"""Stills for hitler_americans.json — one per chunk.

No Nazi flags, no swastikas, no armbands, no camps, no war-gore.
HERO is a stylized 1930s German official (graphic-novel, not a photo).
Movie coverage: hero is NOT in every frame.
"""

from __future__ import annotations

HERO = (
    "HERO (same man every time): stylized graphic-novel 1930s German head of state, "
    "dark side-parted hair, small dark mustache, pale intense face, cold pale eyes, "
    "ALWAYS the same charcoal three-piece suit and plain dark tie, NO medals, "
    "NO armbands, NO symbols, painterly, NOT a photograph, NOT photoreal."
)

AMERICAN = (
    "AMERICAN (same man every time): late-thirties everyman, short brown hair, weary "
    "small dark eyes, slightly oversized round cartoon head that still sits on his neck, "
    "average build, clothes change with the scene, not a celebrity."
)

WORKER = (
    "WORKER (same man): American factory welder, 30s, short dark hair, tired honest face, "
    "coveralls, not a celebrity, not the cartoon everyman."
)

NO_NAZI = (
    "NO swastika, NO Nazi flag, NO SS runes, NO armbands, NO camps, NO Holocaust imagery, "
    "NO gore, NO celebrity politician faces. "
)

STYLE_PEOPLE = (
    "Award-shot 16:9 anamorphic movie still FILLING THE ENTIRE FRAME edge to edge, "
    "no letterbox, no pillarbox, no black bars. Rich color, film grain, motivated lighting, "
    "warm amber and cold graphite, painterly graphic-novel, drop-dead cinematic composition. "
    "No readable text, letters, numbers, logos, watermarks, captions. "
    + NO_NAZI + HERO + " " + AMERICAN + " " + WORKER
)

STYLE_EMPTY = (
    "Award-shot 16:9 anamorphic movie still FILLING THE ENTIRE FRAME edge to edge, "
    "no letterbox, no pillarbox, no black bars. Rich color, film grain, motivated lighting, "
    "warm amber and cold graphite, painterly graphic-novel. STRICTLY NO people, NO faces, "
    "NO hands, NO human silhouettes. No readable text, letters, numbers, logos, watermarks, captions. "
    + NO_NAZI
)

# (shot_type, who, scene)
STILLS: list[tuple[str, str, str]] = [
    ("medium shot", "hero", "HERO looking into camera, a tiny cartoon American flag pin on a desk map of nowhere. He thought it was a cartoon."),
    ("wide shot", "american", "1930s movie-palace screen: a cowboy and a gum-smile close-up, AMERICAN in the front row, radio glow. Page one energy."),
    ("top-down flatlay", "empty", "Page one of a thick folder, a cowboy still clipped on, a cheap pencil. Stay. No people."),
    ("medium shot", "hero", "HERO looking up from the folder. The sentence he got wrong is still unread. Stay."),
    ("medium shot", "hero", "HERO in a night office, not losing sleep, clock glowing. I did not hate you."),
    ("aerial", "empty", "Night aerial of a store parking lot with fireworks, empty cars. A store with fireworks. No people visible."),
    ("wide shot", "crowd", "AMERICAN clapping at himself in a mirror-lined hall, other extras clapping too. A store that clapped at itself. NO HERO."),
    ("low angle", "hero", "HERO on a balcony, a tiny angry crowd with blank signs below. They say a name like a curse."),
    ("over-the-shoulder", "hero", "Over HERO's shoulder: a lineup of identical AMERICAN cartoon faces, one circled."),
    ("medium shot", "hero", "HERO pinning a cartoon drawing of AMERICAN onto a board. That was the mistake."),
    ("medium shot", "american", "AMERICAN in a 1930s cinema, face lit by the screen, believing a movie is a person."),
    ("extreme close-up", "empty", "Giant white teeth beside a car as big as a boat, chrome, steam. Macro. No people."),
    ("wide shot", "american", "Ballroom kiss, a girl kissing a stranger because a band is playing, AMERICAN watching from the door."),
    ("dutch angle", "american", "Ballpark bleachers, AMERICAN chewing gum like the world is a game, soda, daylight."),
    ("extreme close-up", "empty", "Shoes on a theater seat, gum under the chair. No people."),
    ("two-person shot", "american", "Diner, AMERICAN talking to a waiter like a cousin, neon, comedy."),
    ("symbolic graphic", "empty", "A belt left unbuckled on a desk beside a tiny flag pin. Country with no belt. No people."),
    ("wide shot", "american", "A jazz club that will not sit still, AMERICAN dancing in the aisle, brass, smoke. No symbols."),
    ("wide shot", "empty", "Empty Hollywood soundstage, lights, a ticket stub on the floor. Factory of feelings. No people."),
    ("extreme close-up", "empty", "A ticket stub and a film reel, dust. Feelings by the pound. No people."),
    ("wide shot", "crowd", "Movie ending, audience clapping, then smash to airplane cabin clapping, AMERICAN in both as a match-cut energy. NO HERO."),
    ("wide shot", "american", "A man in a hat on a small-town bandstand, AMERICAN clapping, bunting with no slogans."),
    ("symbolic graphic", "empty", "A stack of clapping-hand sculptures, no faces. No other language. No people."),
    ("medium shot", "hero", "HERO stamping a photocopied smile onto an index card. Logging it."),
    ("medium shot", "american", "AMERICAN grinning at a shop clerk who does not smile, coins on the counter."),
    ("symbolic graphic", "empty", "A heart icon outweighing a chess king. Liked more than winning. No people."),
    ("medium shot", "hero", "HERO at an X-ray lightbox of a Hollywood still, butcher-clinical."),
    ("wide shot", "american", "Empty cinema, hero-on-screen kicking a door, AMERICAN in the front row, popcorn."),
    ("extreme close-up", "empty", "Gold sound rings around an empty podium. War ending as music. No people."),
    ("medium shot", "hero", "HERO in the dark theater, AMERICAN glowing across the aisle. Useful. For a while."),
    ("wide shot", "american", "Panelled anteroom, AMERICAN about to enter, cardboard tourist already in the chair with popcorn."),
    ("two-person shot", "american", "AMERICAN arguing with the cardboard cutout. Popcorn. Clock."),
    ("medium shot", "american", "Same argument, twenty minutes on the clock, finger at cardboard."),
    ("symbolic graphic", "empty", "A consistency meter stuck on CARTOON. Personality. No people."),
    ("top-down flatlay", "empty", "Thin expensive folder vs fat cheap one. Cost. No people."),
    ("extreme close-up", "empty", "A 1930s microphone, a crowd as bokeh lights. You said everything. No people."),
    ("top-down flatlay", "empty", "Receipts, tickets, red scoring marks. Nobody watching. No people."),
    ("wide shot", "american", "Box office, AMERICAN choosing the cheaper ticket, a crumpled principle in the bin."),
    ("medium shot", "american", "AMERICAN posting a sunset-looking postcard while sliding a rate napkin."),
    ("wide shot", "american", "Dinner table of men who already exchanged a look; AMERICAN leaning in, hungry to be clever."),
    ("top-down flatlay", "empty", "Clean ledger beside a dusty cash box. Ego vs paper. No people."),
    ("wide shot", "hero", "HERO touring an empty factory catwalk, American flags as bokeh cloth, no symbols."),
    ("two-person shot", "american", "Older host mentioning a paper, AMERICAN lighting up; HERO in far bokeh, taking a note."),
    ("high angle", "hero", "HERO looking down at an empty velvet seat with a tiny folded map on it."),
    ("medium shot", "hero", "HERO writing in a notebook, half-smile that is not kindness."),
    ("wide shot", "american", "AMERICAN proud under bunting, citizen posture, a storefront salute in the glass."),
    ("aerial", "empty", "Market stall lights, crash of a toy cart, fireworks. Market that learned to salute. No people visible."),
    ("symbolic graphic", "empty", "Crashed toy cart, new paint, same dented wheel. New slogan, same hunger. No people."),
    ("medium shot", "hero", "HERO looking into camera, folder open. The sentence he got wrong."),
    ("extreme close-up", "empty", "A typed line on paper, too small to read, a red X not yet drawn. They will not come. No people."),
    ("wide shot", "american", "AMERICAN on a sofa with a radio and an ice-cream dish, arguing at the set, staying home."),
    ("medium shot", "american", "AMERICAN screenshot-energy: holding a newspaper clipping proud, HERO's lamp in a tiny reflection."),
    ("medium shot", "hero", "HERO seeing himself as a tiny fool sketched in the margin of the page. The mistake arriving."),
    ("medium shot", "hero", "HERO at a night window, steel mills glowing far away. Now the number. Respecting the hardware."),
    ("aerial", "empty", "God's-eye of shipyards, cranes, a hull like a poured statue. Steel. No people visible."),
    ("low angle", "hero", "Same HERO, low angle, huge window. I was not lying."),
    ("medium shot", "hero", "HERO, a crack of worry, still not enough. That should have worried me more."),
    ("symbolic graphic", "empty", "Steel I-beam vs slack frayed rope. Receipt vs mood. No people."),
    ("wide shot", "crowd", "A committee room arguing, empty water glasses, a clock, AMERICAN in the gallery."),
    ("wide shot", "american", "Isolation-speech bunting, then a baseball diamond at dusk, AMERICAN in the stands. Then baseball."),
    ("extreme close-up", "empty", "A chalkboard short red line, a stopwatch. The number. No people."),
    ("wide shot", "american", "AMERICAN yelling at a radio, then bored on the couch, then walking out with a coat."),
    ("wide shot", "empty", "Football-field lights on empty bleachers, a long job left as a sticky note. No people."),
    ("medium shot", "hero", "HERO stamping VICTORY on a card, then pausing, the stamp in mid-air. File it under stupid."),
    ("medium shot", "hero", "HERO calm with three crisis radios and a tiny ball-game speaker, tea. Busy."),
    ("symbolic graphic", "empty", "Giant speaker with a mute glyph, city lights. Giant on mute. No people."),
    ("extreme close-up", "empty", "A store shutter down, mute. How a store stays a store. No people."),
    ("medium shot", "soldier", "Tired ordinary 1940s American soldier, still, file-photo light. Not a coward. Not HERO."),
    ("wide shot", "soldier", "A duffel, a porch, phones as 1940s cameras, comments as red dots in the air. Home when pictures get bad."),
    ("extreme close-up", "empty", "Stack of printed photos, a news bezel. Pictures. No identifiable faces."),
    ("extreme close-up", "empty", "News glow on a pack of chewing gum. Callback. No people."),
    ("extreme close-up", "empty", "The gum pack filling the frame again. Until it was not. No people."),
    ("medium shot", "hero", "HERO underlining a page so hard the paper fuzzes. Sit up."),
    ("wide shot", "hero", "HERO watching a movie ending in a dark room, sure he knows the credits. He does not."),
    ("wide shot", "american", "On-screen hero late to the speech, AMERICAN clapping, credits as light bars. No readable type."),
    ("medium shot", "hero", "HERO standing as if the credits already ran, the reel still spinning. I had not."),
    ("top-down flatlay", "empty", "November calendar, gym card, campaign ribbon. Mood dies. No people."),
    ("extreme close-up", "empty", "A campaign song-sheet with no lyrics large enough to read. No people."),
    ("symbolic graphic", "empty", "A wall calendar vs a pair of work gloves. Calendars do not fight. No people."),
    ("symbolic graphic", "empty", "Two circus hats on an empty stand. Different hats. No people."),
    ("wide shot", "american", "A fireside radio, AMERICAN listening to a warm voice, living room, 1930s lamp."),
    ("wide shot", "crowd", "People arguing in rain until the argument looks like weather. AMERICAN filming with a box camera."),
    ("aerial", "empty", "Rain over a factory that does not care about weather. No people visible."),
    ("extreme close-up", "empty", "A calendar Sunday circled too lightly. The day nobody marked enough. No people."),
    ("wide shot", "empty", "Smoke on a grey harbour, a newspaper photo of a flag, no ships exploding, no gore. No people."),
    ("medium shot", "hero", "HERO checking a wristwatch, not gasping. I should have checked the steel."),
    ("medium shot", "both", "AMERICAN accusing HERO of wanting division, cute finger; HERO almost amused. Cute."),
    ("extreme close-up", "empty", "Car engine vs exhaust. Attention vs division. No people."),
    ("medium shot", "hero", "HERO realizing the camera is now on him. He does not like the plot twist."),
    ("extreme close-up", "empty", "An unused movie ticket, torn. Had not paid for that ticket. No people."),
    ("top-down flatlay", "empty", "Stack of printed op-eds, funded. Fights you publish. No people."),
    ("wide shot", "american", "University panel, sandwiches, blank decline banner, AMERICAN nodding in a nearly empty hall."),
    ("wide shot", "crowd", "Celebrity-looking extra at a podium, folded map in a bag, excellent lighting. Not a real celebrity."),
    ("medium shot", "hero", "HERO taking notes under beauty lights, then looking at the notes like they betrayed him."),
    ("top-down flatlay", "empty", "Tote bag, microphone, mailing list as grey bars. Choir merch. No people."),
    ("wide shot", "american", "AMERICAN already screaming, given a huge empty hall and a mic."),
    ("aerial", "empty", "Shipyard still moving, ignoring the screaming hall. It did not stop the ships. No people visible."),
    ("wide shot", "american", "Buffet of idea-posters, spoons, AMERICAN filling a plate."),
    ("extreme close-up", "empty", "Two spoons locked in a fight, chef hat on a hook. No people."),
    ("symbolic graphic", "empty", "Empty spy coat, ignored cash. Not a spy. No people."),
    ("medium shot", "american", "Sincere AMERICAN at a 1930s newsreel camera, unpaid, righteous, being real."),
    ("wide shot", "empty", "Frosted park bench, dark coat, sealed envelope unused. The villain you wanted. No people."),
    ("extreme close-up", "empty", "Envelope opened: a printed quote page, type too small to read. No people."),
    ("medium shot", "hero", "HERO holding the quote page, not editing it. You wrote my jokes."),
    ("medium shot", "hero", "HERO grim at handwriting he does not like. The ending was not his."),
    ("medium shot", "hero", "HERO turning from the cartoon movie to a darker doorway. Now the other American."),
    ("wide shot", "american", "AMERICAN face-lit by a huge screen, alone. The movies are for you."),
    ("wide shot", "worker", "FACTORY WORKER on a hull, sparks, no speech, HERO a speck on a far catwalk."),
    ("tracking", "empty", "Dolly along an assembly line that does not stop, empty of faces, just steel and motion. No people."),
    ("aerial", "empty", "A quiet fleet in grey water, dawn. Quiet built a fleet. No people visible."),
    ("two-person shot", "worker", "WORKERS talking at a lunch pail, then the line moving behind them at dinner light."),
    ("symbolic graphic", "empty", "Ballot box vs welding torch, torn page of one language. Votes vs welds. No people."),
    ("extreme close-up", "empty", "Smoke in a glass ashtray, a late clock. Late tastes like smoke. No people."),
    ("wide shot", "crowd", "A senator-looking extra at a stay-out podium, HERO in the back not cheering. Not a celebrity likeness."),
    ("top-down flatlay", "empty", "A filed speech in a cabinet. Filing is not winning. No people."),
    ("extreme close-up", "empty", "Ugly chewed pencil, three notches. The pencil outlived the mood. No people."),
    ("aerial", "empty", "Ships on the grey water, the mood gone. No people visible."),
    ("extreme close-up", "empty", "Gears, oil, jam light. Machine. Macro. No people."),
    ("extreme close-up", "empty", "Needle in the red, repeating waveform. Same noise. No people."),
    ("wide shot", "crowd", "Crowd filming a smoking machine, pointing at each other. AMERICAN in front."),
    ("symbolic graphic", "empty", "Coin in mid-air over fireworks. I bet on the jam. No people."),
    ("wide shot", "empty", "The same machine ejecting a helmet and a duffel onto a belt. Spat out a war. No people."),
    ("symbolic graphic", "empty", "A giant eye in a mirror, an ocean only in the reflection. Favorite line. No people."),
    ("medium shot", "hero", "HERO saying it until he believes it, empty chairs, rain window."),
    ("wide shot", "worker", "WORKER staring at a factory poster, a boy with a duffel, the sea looking smaller behind glass."),
    ("extreme close-up", "empty", "A joke written on a napkin next to a map with a shortened ocean. No readable names. No people."),
    ("wide shot", "american", "Three years later, AMERICAN watching a sad-piano documentary on a small set."),
    ("extreme close-up", "empty", "Popcorn beside the pause-bar glow. Callback. No people."),
    ("medium shot", "hero", "HERO placing the popcorn still back in the folder. I told you I would bring it back."),
    ("top-down flatlay", "empty", "A movie speech page vs a long paper list. No readable names. No people."),
    ("medium shot", "hero", "HERO seeing a tiny version of himself on a list, AMERICAN's souvenir-shirt energy in bokeh."),
    ("symbolic graphic", "empty", "Unplugged marquee bulbs. Evil is a movie word. No people."),
    ("extreme close-up", "empty", "A clock that was late, then suddenly on time. No people."),
    ("medium shot", "hero", "HERO looking at camera, the compliment tasting bad. Worst thing I can say."),
    ("medium shot", "hero", "HERO, dry. You earned it. Not a gift."),
    ("wide shot", "american", "New AMERICAN on a stage, teleprompter, never-again, merch in the wings. Not a celebrity."),
    ("extreme close-up", "empty", "Wet-ink line on a speech page, a brand tag in a bag. No people."),
    ("medium shot", "hero", "HERO does not cheer, opens the same folder, kettle steam. Panic is mine."),
    ("top-down flatlay", "empty", "Cartoon tab, gum pack, soldier photo face-down. Same guts. No names."),
    ("extreme close-up", "empty", "A duffel, mean-comment red storm, no faces."),
    ("extreme close-up", "empty", "A page circled until torn: they came anyway. Fibers, red pencil. No people."),
    ("tracking", "empty", "Dolly along unmoved headings, photographs changing, empty corridor. No people."),
    ("extreme close-up", "empty", "A file that does not wrinkle beside a mirror that does. No people."),
    ("medium shot", "both", "HERO looking at AMERICAN as he is: loud coat, late, impatient. I needed you you."),
    ("wide shot", "american", "AMERICAN first in line for a sequel poster with ridiculous explosions, popcorn."),
    ("medium shot", "hero", "HERO almost nodding at the explosions, then shaking his head at the ending."),
    ("POV", "american", "POV of the watcher asking if he was right, faint reflection of AMERICAN."),
    ("wide shot", "crowd", "Comment-bright room, AMERICANS fighting monster vs prophet, nobody at the dark window."),
    ("extreme close-up", "empty", "Last page, a gum wrapper, a trap-box unchecked. No people."),
    ("medium shot", "hero", "HERO refusing the prophet trophy, pointing at a factory window instead."),
    ("medium shot", "american", "Someone new as AMERICAN writing the old sentence, slogans in the trash."),
    ("extreme close-up", "empty", "Three dead slogan buttons in a drawer. No people."),
    ("medium shot", "hero", "HERO in a cold room, sharpening a pencil, steam, not dramatic. Maintenance."),
    ("symbolic graphic", "empty", "Gold trophy left on a hook, unearned. Not a genius. No people."),
    ("extreme close-up", "empty", "A sticky-note compliment covering a THINK switch left off. No people."),
    ("wide shot", "both", "AMERICAN walking the same looping wet street; HERO already at the desk. Familiar."),
    ("aerial", "empty", "God's-eye of the looping street and the same puddle. Most expensive free thing. No people visible."),
    ("medium shot", "hero", "HERO closing the folder, the bill arriving in his eyes. I paid later."),
    ("medium shot", "hero", "HERO looking into camera: send this to someone who thinks the cartoon is the whole country."),
    ("medium shot", "hero", "HERO, dry toast. They will not thank you. The file will."),
]


def prompt_for(who: str, scene: str) -> str:
    if who == "empty":
        return f"{STYLE_EMPTY} SCENE: {scene}"
    extras = {
        "hero": "Only HERO on camera unless the scene names someone else in bokeh. Same charcoal three-piece every time. NO symbols.",
        "american": "AMERICAN is the lead. HERO is absent unless the scene names him.",
        "both": "HERO and AMERICAN both visible, locked faces.",
        "worker": "WORKER is the lead. HERO only if named as a speck. Cartoon AMERICAN is absent unless named.",
        "soldier": "Tired ordinary 1940s American soldier, not a celebrity, not HERO, not the cartoon AMERICAN.",
        "crowd": "Generic extras, not celebrities. Recurring leads only if named. NO politician faces. NO symbols.",
    }
    return f"{STYLE_PEOPLE} {extras.get(who, '')} SCENE: {scene}"
