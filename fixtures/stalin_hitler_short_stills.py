"""Vertical 9:16 stills for Stalin-Hitler Short v4 (Simple History flat-vector)."""

from __future__ import annotations

PROP_BUDGET = {"THE GLASS": 6}
SET_TOKENS = ["THE KREMLIN"]

HERO = (
    "HERO (same cartoon man every time): Simple History explainer character, FLAT 2D "
    "VECTOR, pale round face, TWO SOLID BLACK DOT EYES, thin line mouth, simple cartoon "
    "mustache, dark hair with a side part, charcoal-grey high-collar tunic, NO medals, "
    "NOT a photograph, NOT a celebrity likeness."
)
GLASS = "THE GLASS (same prop): simple cut-crystal champagne coupe, flat vector."
KREMLIN = "THE KREMLIN (same set): night office, green lamp, heavy brown desk, no flags."
NO_NAZI = "NO swastika, NO Nazi flag, NO armbands, NO camps, NO gore, NO photoreal famous people. "
STYLE = (
    "Vertical 9:16 Simple History explainer still FILLING THE FRAME, no letterbox, "
    "subject large in the upper two thirds, FLAT 2D VECTOR, solid colors, dot eyes, "
    "paper-cutout educational animation, red-to-orange gradient OK for portraits. "
    "No readable text. "
    + NO_NAZI + HERO + " " + GLASS + " " + KREMLIN
)

STILLS: list[tuple[str, str, str]] = [
    ("medium shot", "hero", "HERO looking into camera, teaching the simple thought. Grey tunic. NO symbols."),
    ("wide shot", "empty", "An empty road, the bad man leaving him alone. Flat vector. No people."),
    ("medium shot", "hero", "HERO lifting THE GLASS at two in the morning. NO symbols."),
    ("wide shot", "crowd", f"{KREMLIN} The room smiles, he thinks the paper made the bad man safe. THE GLASS in hand."),
    ("medium shot", "hero", f"{KREMLIN} HERO drawing a line on a map, sending food, a birthday envelope. NO symbols."),
    ("wide shot", "empty", "A wooden house with lights on, the house you don't wish birthday into. No people."),
    ("wide shot", "empty", "Lights in the trees he says are nothing. No people."),
    ("medium shot", "empty", f"{KREMLIN} Phone ringing, Sunday still night. No people."),
    ("medium shot", "hero", "HERO at the phone, it is not a friend. NO symbols."),
    ("wide shot", "hero", f"{KREMLIN} Through a window: unfinished toast, story waiting. NO symbols."),
]


def prompt_for(who: str, scene: str) -> str:
    return f"{STYLE} SCENE: {scene}"
