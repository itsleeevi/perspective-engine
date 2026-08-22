"""Stills for stalin_hitler.json v4 — Simple History flat-vector, same v3 story.

Signature prop: THE GLASS in ≤6 scenes. Sets: THE KREMLIN, THE DACHA.
Look: educational 2D explainer (dot eyes, solid colors), not painterly cinema.
"""

from __future__ import annotations

PROP_BUDGET = {"THE GLASS": 6}
SET_TOKENS = ["THE KREMLIN", "THE DACHA"]

HERO = (
    "HERO (same cartoon man every time, do not redesign): Simple History / educational "
    "YouTube explainer character, FLAT 2D VECTOR, geometric shapes, pale round face, "
    "TWO SOLID BLACK DOT EYES, thin arched eyebrows, small straight-line mouth, "
    "a simple cartoon mustache as a small black mark, dark hair combed with a side part, "
    "ALWAYS the same charcoal-grey high-collar tunic buttoned to the neck, NO medals, "
    "NO stars, NO gold braid, NOT a photograph, NOT photoreal, NOT a celebrity likeness."
)
GUEST = (
    "THE GUEST (same cartoon man): tall silver-haired diplomat, same flat-vector "
    "dot-eye construction, black double-breasted coat, high white collar, NO symbols, "
    "NOT a celebrity likeness, not HERO."
)
AIDE = (
    "AIDE (same cartoon man): round-faced foreign-ministry official, pince-nez, dark suit, "
    "same dot-eye flat-vector construction, not HERO, not a celebrity."
)
MARSHAL = (
    "MARSHAL (same cartoon man): field commander, peaked cap without emblems, khaki tunic, "
    "same dot-eye flat-vector construction, not HERO."
)
GLASS = (
    "THE GLASS (same prop every time): one simple cut-crystal champagne coupe, "
    "flat vector, short stem, a yellow highlight in the bowl."
)
KREMLIN = (
    "THE KREMLIN (same set): night office as Simple History interior, green lamp, "
    "heavy brown desk, no flags, no emblems, no readable text."
)
DACHA = (
    "THE DACHA (same set): small wooden country house among simple pine triangles, "
    "a black telephone, grey daylight, no flags."
)
NO_NAZI = (
    "NO swastika, NO Nazi flag, NO SS runes, NO armbands, NO camps, NO gore, "
    "NO celebrity politician faces, NO photoreal famous people. "
)
LOOK = (
    "Simple History YouTube explainer still: FLAT 2D VECTOR illustration FILLING THE "
    "ENTIRE 16:9 FRAME edge to edge, no letterbox, no pillarbox, no black bars, no film "
    "grain, no painterly brushwork, no 3D, no photorealism. Clean outlines, solid color "
    "blocks, paper-cutout educational animation. Portrait shots may use a vertical "
    "red-to-orange gradient background. Scene shots use muted earth tones: charcoal, "
    "olive, ochre, brick red, cream, teal. No readable text, letters, numbers, logos, captions. "
)
STYLE_PEOPLE = LOOK + NO_NAZI + HERO + " " + GUEST + " " + AIDE + " " + MARSHAL + " " + GLASS
STYLE_EMPTY = (
    LOOK
    + "STRICTLY NO people, NO faces, NO hands. "
    + NO_NAZI
    + GLASS
    + " "
)

# THE GLASS in 005, 006, 009, 050, 051, 054
STILLS: list[tuple[str, str, str]] = [
    ("medium shot", "hero", "HERO looking into camera, the simple thought on his face: if I am nice, I stay safe. Grey-green tunic. NO symbols."),
    ("wide shot", "empty", "An empty dark road leading away from a small house, the bad man leaving him alone. No people."),
    ("medium shot", "hero", "HERO holding up one finger as if teaching a child the idea. Pipe. NO symbols."),
    ("wide shot", "empty", "A smiling room implied by empty chairs and flash-powder haze, a scary silhouette walking the other way. No people."),
    ("medium shot", "empty", f"{KREMLIN} Wet ink on a cream paper at two in the morning, lamp. No people."),
    ("medium shot", "hero", "HERO lifting THE GLASS, drinking to the other man's health. Grey-green tunic. NO symbols."),
    ("wide shot", "crowd", f"{KREMLIN} The room smiling, photographers, HERO with THE GLASS, he thinks the paper worked."),
    ("aerial", "empty", "A faraway city on fire, the fight going somewhere else, not here. No people."),
    ("wide shot", "empty", "Empty snow fields near home, not here. No people."),
    ("medium shot", "hero", "HERO smiling with THE GLASS, a helper in his head. NO symbols."),
    ("medium shot", "hero", "HERO at a huge desk like a child running a country on a simple deal. NO symbols."),
    ("medium shot", "hero", "HERO at a night window, scared, needing a helper. NO symbols."),
    ("wide shot", "empty", "Empty army chairs, the men who knew how to fight gone. No people."),
    ("medium shot", "hero", "HERO checking a clock, needing time. NO symbols."),
    ("aerial", "empty", "Fire staying in someone else's house on the horizon. No people."),
    ("top-down flatlay", "empty", "A map with one simple line: that side, this side. No readable names. No people."),
    ("medium shot", "hero", f"{KREMLIN} HERO putting the paper in a drawer. Nobody hits anybody. NO symbols."),
    ("medium shot", "empty", "A child's toy chest closing, MATCH CUT to the drawer closing. We are done. No people."),
    ("aerial", "empty", "Grain trains going away, food sent the other way. No people."),
    ("medium shot", "empty", "A birthday telegram on a blotter, no readable words. Happy birthday. No people."),
    ("wide shot", "empty", "A wooden house, lights on, the house you do not wish a long life into if you think it will burn. No people."),
    ("medium shot", "hero", "HERO handing a small envelope, the man he thinks he's made safe. NO symbols."),
    ("wide shot", "aide", "AIDE under falling dust in a street, bombs, going to talk about oil. NO HERO."),
    ("medium shot", "aide", "AIDE in a basement, finishing the talk underground. Friends do not do this. NO HERO."),
    ("medium shot", "aide", "AIDE looking up at the cellar ceiling: that should have been enough. NO HERO."),
    ("wide shot", "empty", "A spy radio, a letter on wet stone. People trying to warn him. No people."),
    ("wide shot", "empty", "Lights in the trees at night. He hears them. Then he says no. No people."),
    ("wide shot", "empty", "Nine days later the same lights are tank silhouettes. No people."),
    ("medium shot", "hero", f"{KREMLIN} HERO covering his ears over the papers, the simple idea must stay true. NO symbols."),
    ("medium shot", "hero", "HERO shaking his head: if the bad man never listens, the smile was a mistake. NO symbols."),
    ("medium shot", "empty", "Food sacks and a birthday envelope, all mistakes if the idea is wrong. No people."),
    ("wide shot", "empty", "A sleeping barracks, the army left asleep. No people."),
    ("wide shot", "empty", "Last food train after dark, red lamp. No people."),
    ("medium shot", "empty", f"{KREMLIN} Phone ringing in the dark, Sunday. No people."),
    ("wide shot", "empty", "Planes and fire on a tree line, no letter, an army. No gore. No people close."),
    ("medium shot", "hero", "HERO at the phone saying maybe it is only a trick. NO symbols."),
    ("medium shot", "hero", "HERO's face: a trick you talk about, an army you cannot. NO symbols."),
    ("wide shot", "hero", "HERO leaving the city at dawn, the simple idea wrong. NO symbols."),
    ("medium shot", "hero", f"{DACHA} HERO in a little house in the trees, not answering the phone. NO symbols."),
    ("extreme close-up", "empty", "A black telephone ringing for days. No people."),
    ("wide shot", "hero", f"{DACHA} HERO small, hiding, the story he told himself broken. NO symbols."),
    ("medium shot", "empty", "A coupe, a map line, a birthday envelope — he smiled, he drew, he sent. Objects only. No people."),
    ("wide shot", "empty", "Fire at his fence, the bad man in his house. No people."),
    ("medium shot", "hero", "HERO with empty hands, no other story left. NO symbols."),
    ("wide shot", "hero", "HERO walking back toward fire. The fire does not wait. NO symbols."),
    ("wide shot", "empty", "Dawn window, this morning, not later speeches. No people."),
    ("medium shot", "empty", "A piece of paper on a table, as if paper could make a bad man good. No people."),
    ("aerial", "empty", "Winter fields, a lot of people died, no bodies, no gore, just scale. No people visible."),
    ("wide shot", "empty", "An open door, safety he thought he bought, only time for the other man. No people."),
    ("medium shot", "hero", "HERO looking at a clock he cannot buy. NO symbols."),
    ("extreme close-up", "empty", "THE GLASS from the toast, empty, dust. Last picture. No people."),
    ("medium shot", "empty", "THE GLASS on the wooden table in the little house. He drank with the man. No people."),
    ("medium shot", "hero", "HERO leaning in as if telling a child one more time. NO symbols."),
    ("medium shot", "hero", "HERO, the thought on his face again: if he was nice, he would be left alone. NO symbols."),
    ("medium shot", "hero", "HERO looking at the empty guest chair. THE GLASS on the table. The bad man did not. NO symbols."),
]


def prompt_for(who: str, scene: str) -> str:
    if who == "empty":
        return f"{STYLE_EMPTY} SCENE: {scene}"
    extras = {
        "hero": "Only HERO unless the scene names someone else. Same charcoal-grey tunic. THE GLASS only if named. NO symbols.",
        "aide": "AIDE is the lead. HERO absent.",
        "marshal": "MARSHAL is the lead. HERO absent.",
        "crowd": "Generic extras, not celebrities. NO politician faces. NO symbols. NO HERO unless named.",
    }
    return f"{STYLE_PEOPLE} {extras.get(who, '')} SCENE: {scene}"
