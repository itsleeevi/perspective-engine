"""v5 movie stills for putin_americans.json — one per chunk.

No Ukrainian flags, no blue-and-yellow, no war-in-Ukraine imagery.
Trump exists only as off-face rally energy (red hats from behind, a gold
phone at 3am). Never a photoreal celebrity. Never a named politician's face.

Locked leads:
  HERO     — stylized graphic-novel Russian president
  AMERICAN — cartoon everyman the VO is roasting
  OTHER    — quiet rich American
Hero is NOT in every frame.
"""

from __future__ import annotations

HERO = (
    "HERO (same man every time): stylized graphic-novel Russian president, "
    "short pale thinning hair, lined pale face, thin unsmiling mouth, small cold "
    "grey-blue eyes, compact athletic build, ALWAYS the same dark navy three-piece "
    "suit and small gold watch, painterly, NOT a photograph, NOT photoreal."
)

AMERICAN = (
    "AMERICAN (same man every time): late-thirties everyman, short brown hair, "
    "weary small dark eyes, slightly oversized round cartoon head that still sits "
    "on his neck, average build, clothes change with the scene, not a celebrity."
)

OTHER = (
    "OTHER AMERICAN (same man): silver-grey hair, expensive quiet dark coat, "
    "no logos, thinner face, not a celebrity, not the everyman."
)

NO_FLAGS = (
    "NO Ukrainian flag, NO blue-and-yellow flag, NO war footage, NO missiles, "
    "NO celebrity politician faces, NO photoreal famous people. "
)

STYLE_PEOPLE = (
    "Award-shot 16:9 anamorphic movie still, rich color, film grain, motivated "
    "lighting, olive gold and cold teal, painterly graphic-novel, drop-dead "
    "cinematic composition. No readable text, letters, numbers, logos, watermarks, "
    "captions. "
    + NO_FLAGS + HERO + " " + AMERICAN + " " + OTHER
)

STYLE_EMPTY = (
    "Award-shot 16:9 anamorphic movie still, rich color, film grain, motivated "
    "lighting, olive gold and cold teal, painterly graphic-novel, stunning "
    "empty-frame composition. STRICTLY NO people, NO faces, NO hands, NO human "
    "silhouettes. No readable text, letters, numbers, logos, watermarks, captions. "
    + NO_FLAGS
)

# (shot_type, who, scene)
STILLS: list[tuple[str, str, str]] = [
    ("wide shot", "crowd", "Airplane cabin just after landing, passengers clapping like a theater, AMERICAN in the aisle seat clapping too, unimpressed flight attendant. STRICTLY NO HERO, no navy-suit president."),
    ("medium shot", "hero", "HERO at a steel desk, holding a photo of that clapping cabin, folder open, rain window. Page one."),
    ("top-down flatlay", "empty", "Page one of a thick folder, a small cabin photo clipped on, a cheap pencil. Funny first, then not. No people."),
    ("medium shot", "hero", "HERO looks into camera, folder half-closed. The next pages are not a joke. Stay."),
    ("medium shot", "hero", "HERO in the night office, not losing sleep, clock glowing. I do not hate you."),
    ("symbolic graphic", "empty", "A wall calendar, Tuesday pinned, rain on the window, a credit-card hologram shimmer. Weather. No people."),
    ("low angle", "hero", "HERO on a balcony above a tiny angry crowd with blank signs. They yell. He already knows the type."),
    ("over-the-shoulder", "hero", "Over HERO's shoulder: a lineup of identical AMERICAN faces, one circled. Easy to guess."),
    ("extreme close-up", "empty", "A row of dusty flip phones, years as objects. Waiting you out. No people."),
    ("medium shot", "american", "AMERICAN on a couch, face lit by a CRT, junk living room, believing a commercial."),
    ("extreme close-up", "empty", "A sandwich as big as a steering wheel, steam, ridiculous scale, white-tooth gleam at the edge. No people."),
    ("extreme close-up", "empty", "Giant red soda cup, ice, condensation, big enough for a terrier. Macro. No people."),
    ("wide shot", "american", "Too-bright fake kitchen, AMERICAN family frozen mid-hug under movie lights, cash and a clapper on the counter."),
    ("POV", "american", "POV from the couch at the commercial, a house-shaped cookie tin, homesick empty living room."),
    ("symbolic graphic", "empty", "Gold jingle sound-waves over a black confession-booth silhouette. That is you, with a song. No people."),
    ("dutch angle", "american", "Packed diner canted, AMERICAN shouting over plates, neon, nobody else getting a word in."),
    ("two-person shot", "american", "Waiter deadpan with a pad, AMERICAN leaning in with life-advice energy. Comedy."),
    ("medium shot", "american", "AMERICAN in a huge unreadable chest mark walking a sidewalk as a human billboard."),
    ("extreme close-up", "empty", "A logo-shaped blank patch of fabric filling the frame, stitching, walking-ad cloth. No people."),
    ("wide shot", "crowd", "Same airplane cabin, passengers mid-clap, AMERICAN still clapping, attendant unimpressed. Callback. NO HERO."),
    ("extreme close-up", "empty", "Two hands clapping in an airplane aisle, tray tables, no faces. You still clap. No identifiable people."),
    ("wide shot", "american", "Drab classroom, AMERICAN at a desk, chalkboard stick-figure with a sleeve flag, a blank map with no country colors."),
    ("top-down flatlay", "empty", "A stamped INSTRUCTIONS stencil on manila, coffee ring, chalk dust. Not an insult. No people."),
    ("medium shot", "hero", "HERO stamping a photocopied smile onto an index card. Logging it. Clinical."),
    ("medium shot", "american", "AMERICAN grinning at a cashier who does not smile, overcharge receipt in his hand."),
    ("symbolic graphic", "empty", "A heart icon outweighing a chess king on a scale. Liked more than winning. No people."),
    ("extreme close-up", "empty", "A like-button glow, cold, no face. Winning does not get a like. No people."),
    ("medium shot", "hero", "HERO at an X-ray lightbox of a Hollywood still, butcher-clinical, cow-hook shadow."),
    ("wide shot", "american", "Empty cinema, action-hero on screen kicking a door, AMERICAN in the front row, popcorn, mouth open."),
    ("extreme close-up", "empty", "Gold sound rings around an empty podium, a fight ending as music. No people."),
    ("medium shot", "hero", "HERO in the dark theater, AMERICAN glowing in the screen-light across the aisle. I believe that you do."),
    ("wide shot", "american", "Panelled anteroom, AMERICAN about to enter, cardboard tourist already in the far chair with chips."),
    ("two-person shot", "american", "AMERICAN arguing with the cardboard cutout. Chips. Clock. The cartoon arrived first."),
    ("medium shot", "american", "Same argument, twenty minutes on the clock, AMERICAN jabbing a finger at cardboard."),
    ("symbolic graphic", "empty", "A consistency meter stuck on CARTOON vs a jumping human needle. Personality. No people."),
    ("top-down flatlay", "empty", "Thin expensive folder vs fat cheap one, gold clip vs rust. Cost. No people."),
    ("top-down flatlay", "empty", "Receipts, boarding pass, red scoring marks, nobody watching. No people."),
    ("wide shot", "american", "Airport kiosk, AMERICAN choosing the cheapest fare, a crumpled principle in the bin."),
    ("medium shot", "american", "AMERICAN posting a sunset while sliding a rate napkin across a cafe table."),
    ("wide shot", "american", "Dinner table of men who already exchanged a look; AMERICAN leaning in, hungry to be clever."),
    ("top-down flatlay", "empty", "Clean bank statement beside a dusty closed cash box. Ego vs paper. No people."),
    ("extreme close-up", "empty", "A conference lanyard and blank badge on marble, a velvet rope. Access. No people."),
    ("two-person shot", "american", "Older host mentioning a name, AMERICAN lighting up; HERO in far bokeh, taking a note."),
    ("high angle", "hero", "HERO looking down at an empty velvet theater seat with a tiny toy warhead on it. The joke about a good seat."),
    ("medium shot", "hero", "HERO writing in a notebook, half-smile that is not kindness. Still taking notes."),
    ("wide shot", "american", "AMERICAN proud in a voting-booth curtain, citizen posture, fireworks bloom in the parking lot beyond."),
    ("symbolic graphic", "empty", "Crashed toy cart, new paint, same dented wheel. New color, same product. No people."),
    ("medium shot", "hero", "HERO looking into camera, folder open, delivering the promised sentence. You come back."),
    ("extreme close-up", "empty", "A coupon on steel, underlined twice, return-arrow stamp. Thirsty. No people."),
    ("medium shot", "american", "AMERICAN screenshotting a line on his phone, proud, HERO's lamp in a tiny reflection."),
    ("medium shot", "hero", "HERO already knowing, not looking up. I already knew you would."),
    ("medium shot", "hero", "HERO at a night window, scale-model ship and satellite on the sill, no smile. Now the number."),
    ("low angle", "hero", "Same HERO, low angle, huge window. I am not lying. Slightly threatening comedy."),
    ("symbolic graphic", "empty", "Steel I-beam vs slack frayed rope. Receipt vs mood. No people."),
    ("wide shot", "crowd", "Bright hearing room, people arguing, empty water glasses, a clock running, AMERICAN in the gallery filming."),
    ("extreme close-up", "empty", "A chalkboard short red line, a stopwatch. The number. No people."),
    ("wide shot", "american", "AMERICAN yelling at a TV, then on the couch bored with the remote, then walking out the door with a duffel."),
    ("wide shot", "empty", "Monday-night football glow on an empty living room, pizza box, the long job left on a sticky note. No people."),
    ("medium shot", "hero", "HERO calm with three crisis TVs and a tiny football game in the corner, tea. Busy."),
    ("symbolic graphic", "empty", "Giant speaker with a mute glyph, city lights behind. Superpower on mute. No people."),
    ("medium shot", "soldier", "Tired ordinary soldier in kit, still, file-photo light. Not a coward. Not HERO. Not AMERICAN cartoon head."),
    ("wide shot", "soldier", "Transport-plane ramp, duffel, phones filming, red comment-dots in the night air. Home when pictures get bad."),
    ("extreme close-up", "empty", "Stack of printed bad-news photos, TV bezel. Pictures. No identifiable faces."),
    ("extreme close-up", "empty", "Evening-news glow on the SAME red cup of ice. Callback. No people."),
    ("extreme close-up", "empty", "The red cup filling the frame again. You remember it. That is the point. No people."),
    ("medium shot", "hero", "HERO underlining a page so hard the paper fuzzes, looking up. Sit up."),
    ("wide shot", "crowd", "Movers carrying a kettle through a briefing room as maps of nowhere come down. Absurdist. No country flags."),
    ("wide shot", "american", "Tuesday parade, confetti, a song, a binder on a float, AMERICAN waving from the curb. No blue-yellow flags."),
    ("extreme close-up", "empty", "A gold seal peeling off a slack ribbon. A deal is not a deal. No people."),
    ("top-down flatlay", "empty", "January calendar, expired gym card, a deal paper beside it. Mood dies. No people."),
    ("extreme close-up", "empty", "A wall calendar filling the frame. Calendars do not give speeches. No people."),
    ("symbolic graphic", "empty", "Two circus hats on an empty ringmaster stand, campaign bunting with no slogans. Different hats. No people."),
    ("wide shot", "crowd", "Night rally from behind: a sea of red hats, faces turned away, stage lights, no identifiable politician, no celebrity face."),
    ("extreme close-up", "empty", "A gold smartphone glowing 3:00 on a nightstand, rumpled hotel sheets. Three in the morning. No people."),
    ("match cut", "empty", "Two presidential costumes on hangers swapping places, same empty oval office. Loud guy, other guy, loud guy again. No faces."),
    ("medium shot", "hero", "HERO did not even change chairs, same tea, same window. Presidents are not his problem."),
    ("wide shot", "hero", "HERO circling FIGHT on a chalkboard; a presidential costume on a hanger beside it."),
    ("wide shot", "empty", "Empty campaign street August to November, yard signs with blank shapes, a parked van. Unpaid holiday. No people."),
    ("extreme close-up", "empty", "Cracked marble bust of virtue. Consistency. No people."),
    ("medium shot", "hero", "HERO shrugging at a broken timeline, coffee, snow window. Not his problem."),
    ("medium shot", "hero", "HERO waiting, clock, empty chairs. Spider patience. Not talking you into anything."),
    ("wide shot", "american", "AMERICAN on stage saying the opposite of last year, old clip frozen beside him."),
    ("symbolic graphic", "empty", "Two identical movie tickets for the same sequel. Paid twice. No people."),
    ("top-down flatlay", "empty", "Same fat folder, new title strip, old strip in the trash. New name on the tab. No faces."),
    ("extreme close-up", "empty", "Ugly chewed cheap pencil, three notches in the paint. Three presidents. No people."),
    ("extreme close-up", "empty", "The same chewed pencil even closer, splintered paint, cheap metal ferrule. Not nice. No people."),
    ("top-down flatlay", "empty", "Stack of printed op-eds, funded. Fights you publish. No people."),
    ("wide shot", "american", "University panel, sandwiches, blank decline banner, AMERICAN nodding in a nearly empty hall."),
    ("wide shot", "crowd", "Celebrity-looking extra at a podium, folded map in a bag, cameras, excellent lighting. Not a real celebrity."),
    ("extreme close-up", "empty", "Beauty-light ring, empty stool, excellent lighting, no speaker. No people."),
    ("top-down flatlay", "empty", "Tote bag, podcast mic, mailing list as grey bars. Choir merch. No people."),
    ("match cut", "empty", "Old telegram spike dissolving into a glowing heart-like button. Same muscle. No people."),
    ("wide shot", "american", "AMERICAN already screaming, given a huge empty hall and a mic, spotlight of rage."),
    ("low angle", "american", "Same AMERICAN from below swallowing the room, HERO a speck in the back row."),
    ("wide shot", "american", "Buffet of idea-posters, spoons, AMERICAN filling a plate. Marketplace as food."),
    ("extreme close-up", "empty", "Two spoons locked in a fight, chef hat on a hook, clock at a hungry hour. No people."),
    ("symbolic graphic", "empty", "Empty spy coat, ignored cash bundle. Not a spy. No people."),
    ("medium shot", "american", "Sincere AMERICAN at a kitchen webcam, unpaid, righteous, authenticity lighting."),
    ("extreme close-up", "empty", "Webcam ring-light, a handwritten BEING REAL sticky note. No people."),
    ("wide shot", "empty", "Frosted park bench, dark coat, sealed envelope unused. The villain you wanted. No people."),
    ("extreme close-up", "empty", "Envelope opened: a printed quote page, type too small to read. The quote is yours. No people."),
    ("medium shot", "hero", "HERO holding the quote page, not editing it. You wrote my dialogue."),
    ("medium shot", "hero", "HERO turning from the cartoon TV to a darker doorway. Now the other American."),
    ("wide shot", "american", "AMERICAN face-lit by a huge TV, alone, the cartoon. TV is for you."),
    ("wide shot", "other", "Quiet London hotel bar, OTHER AMERICAN in a dark coat, low lamps, no logos, HERO drinking with him. Through the window a white boat, blank stern."),
    ("medium shot", "other", "OTHER AMERICAN lecturing a camera about democracy at lunch, boom mic, perfect daylight."),
    ("two-person shot", "other", "Same OTHER at dinner, matchbook, loophole question, HERO listening, candles."),
    ("symbolic graphic", "empty", "Street split: ballot box vs invoice stamp, torn page of one language. Two countries. No people."),
    ("extreme close-up", "empty", "A ledger, the invoice column circled. Guess which number. No people."),
    ("wide shot", "other", "Heavy curtains, young man at a private table, waiter blocking a photograph, HERO checking a watch."),
    ("extreme close-up", "empty", "A wristwatch face. No gasp. Just time. Insert. No people."),
    ("extreme close-up", "empty", "Gears, oil, jam light. Machine. Macro. No people."),
    ("extreme close-up", "empty", "Needle in the red, repeating waveform. Same noise before they fail. No people."),
    ("wide shot", "crowd", "Crowd filming a smoking machine with phones, pointing at each other not the gears. AMERICAN in the front. Coin flipping over fireworks in a mural behind."),
    ("symbolic graphic", "empty", "Coin in mid-air over fireworks. Fifty percent plus one. No people."),
    ("medium shot", "both", "AMERICAN accusing HERO of wanting division, cute finger out; HERO almost amused. Cute."),
    ("extreme close-up", "empty", "Car engine vs exhaust pipe. Attention vs division. No people."),
    ("dutch angle", "american", "Supermarket aisle, cereal, AMERICAN saying the wrong three words into a phone, camera already there."),
    ("symbolic graphic", "empty", "Giant eye in a bathroom mirror, a window behind the viewer left unused. Cannot stare out. No people."),
    ("aerial", "empty", "News-week eating a calendar; the world beyond the TV glow keeps moving. God's-eye. No people. No flags."),
    ("wide shot", "american", "Three years later, AMERICAN watching a sad-piano documentary on a laptop."),
    ("extreme close-up", "empty", "The commercial sandwich again beside the laptop pause bar. Callback. No people."),
    ("medium shot", "hero", "HERO placing the sandwich photo back into the folder. I told you I would bring it back."),
    ("symbolic graphic", "empty", "Unplugged movie-marquee bulbs spelling nothing. Evil is a movie word. No people."),
    ("medium shot", "hero", "HERO almost nodding, a cold red check on the enemy file. Nicest thing I say."),
    ("medium shot", "hero", "HERO looking at camera. Congratulations. You earned it."),
    ("wide shot", "american", "New AMERICAN on a political stage, teleprompter, reset, children's merch in the wings. Not a celebrity likeness."),
    ("extreme close-up", "empty", "Wet-ink line on a speech page, a smear of THIS TIME, tiny brand tags in a kid's bag. No people."),
    ("medium shot", "hero", "HERO does not cheer, skipping-rope unused (panic is cardio), opens the same folder, kettle steam."),
    ("top-down flatlay", "empty", "Cartoon tab, coupon, soldier photo face-down. Same guts. No readable names."),
    ("extreme close-up", "empty", "Phone comments as a red storm over a duffel, a red hat on a hanger in bokeh. Mean comments. Loud guy as an object. No faces."),
    ("match cut", "empty", "Two costumes swapping on the hanger again. Other guy. Loud guy again. No faces."),
    ("tracking", "empty", "Dolly along a wall of unmoved headings, photographs changing in frames, dust, empty corridor. No people. No flags."),
    ("extreme close-up", "empty", "A file that does not wrinkle beside a mirror that does. You age. The file does not. No people."),
    ("medium shot", "both", "HERO looking at AMERICAN as he is: loud coat, watch, impatient. I need you you."),
    ("wide shot", "american", "AMERICAN first in line for a sequel poster with ridiculous explosions, popcorn, believing the trailer."),
    ("POV", "american", "POV of the watcher at the end of a video, dark screen, asking if he is right, faint reflection of AMERICAN."),
    ("wide shot", "crowd", "Comment-bright room, AMERICANS fighting genius vs cartoon, nobody at the dark window."),
    ("extreme close-up", "empty", "Last page of the folder, a checked box under a coupon. I predicted that too. No people."),
    ("medium shot", "american", "Someone new as AMERICAN writing the old sentence, coffee, slogans in the trash."),
    ("extreme close-up", "empty", "Three dead slogan buttons in a drawer, older than the new speech. No people."),
    ("medium shot", "hero", "HERO in a cold room, sharpening a pencil, steam, not dramatic. Maintenance."),
    ("symbolic graphic", "empty", "Gold trophy left on a hook, unearned. Not a genius. No people."),
    ("extreme close-up", "empty", "A sticky-note compliment covering a CHANGE switch left off. No people."),
    ("wide shot", "both", "AMERICAN walking the same looping wet street; HERO already seated at the desk, waiting. Familiar."),
    ("aerial", "empty", "God's-eye of the looping street and the same puddle. The most expensive free thing. No people visible."),
    ("medium shot", "hero", "HERO looking into camera, dry toast: send this to someone who clapped. They will not thank you. I will."),
]


def prompt_for(who: str, scene: str) -> str:
    if who == "empty":
        return f"{STYLE_EMPTY} SCENE: {scene}"
    extras = {
        "hero": "Only HERO on camera unless the scene names someone else in bokeh. Same navy three-piece every time.",
        "american": "AMERICAN is the lead. HERO is absent unless the scene names him.",
        "both": "HERO and AMERICAN both visible, locked faces, same wardrobe rules.",
        "other": "OTHER AMERICAN is the lead. HERO only if named. The cartoon everyman is absent unless named.",
        "soldier": "Tired ordinary soldier, not a celebrity, not HERO, not the cartoon AMERICAN.",
        "crowd": "Generic extras, not celebrities. Recurring leads only if named. NO politician faces.",
    }
    return f"{STYLE_PEOPLE} {extras.get(who, '')} SCENE: {scene}"
