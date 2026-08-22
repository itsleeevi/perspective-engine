"""Vertical (9:16) stills for the Hitler-Americans traffic Short.

Same hero, same signature prop, same graphic-novel look as the long video so
the click from Short to long feels continuous — but composed for a phone
screen: tighter frames, subjects higher in frame, bold single focal points.
"""

from __future__ import annotations

PROP_BUDGET = {"THE BOOK": 6}
SET_TOKENS = ["THE OFFICE"]

HERO = (
    "HERO (same man every time, do not redesign): stylized graphic-novel 1930s "
    "European official, dark side-parted hair combed flat, CLEAN-SHAVEN, NO mustache, "
    "pale intense face, cold pale eyes, ALWAYS the same charcoal three-piece suit and "
    "plain dark tie, NO medals, NO armbands, NO symbols, painterly, NOT a photograph."
)

BOOK = (
    "THE BOOK (same prop every time): a cheap German cowboy paperback, soft brown cover, "
    "painted rearing horse, worn spine. It must look like the SAME physical object whenever it appears."
)

OFFICE = (
    "THE OFFICE (same set): 1940s rain-window night office, steel desk, brass lamp. "
)

NO_NAZI = (
    "NO swastika, NO Nazi flag, NO SS runes, NO armbands, NO camps, NO Holocaust imagery, "
    "NO gore, NO celebrity politician faces, NO photoreal famous people. "
)

STYLE = (
    "Vertical 9:16 cinematic movie still for a phone screen, FILLING THE ENTIRE FRAME "
    "edge to edge, no letterbox, no black bars, main subject large and centered in the "
    "upper two thirds. Rich color, film grain, motivated lighting, warm amber and cold "
    "graphite, painterly graphic-novel, drop-dead cinematic composition. "
    "No readable text, letters, numbers, logos, watermarks, captions. "
    + NO_NAZI + HERO + " " + BOOK + " " + OFFICE
)

# (shot_type, who, scene) — 1:1 with the short fixture's 9 chunks at 175 wpm
STILLS: list[tuple[str, str, str]] = [
    ("wide shot", "empty", "1945 Berlin office door kicked inward and splintered, rain blowing in, war maps and overturned chairs beyond, torchlight beams. Urgent. No people visible."),
    ("top-down flatlay", "empty", "THE BOOK lying on top of scattered war maps under a brass lamp, arrows and pencils around it — a cowboy paperback where the battle plans should be. No people."),
    ("extreme close-up", "empty", "THE BOOK huge in frame, half inside an open steel desk drawer, painted rearing horse cover, worn spine, lamp glow. A child's toy in a war machine. No people."),
    ("wide shot", "empty", "Empty New York street canyon at dawn seen from the ground looking up, wet asphalt, towering buildings vanishing into mist, a closed diner window. Nobody. He never stood here. No people."),
    ("medium shot", "empty", "Desk-level cinematic shot, shallow depth: THE BOOK propped upright, a film reel unspooling beside it, a glossy 1930s car brochure leaning against the lamp, projector light flickering across them. His entire knowledge of a continent. No people."),
    ("symbolic graphic", "empty", "A vast dark ocean map, and from the far side an enormous tide of light shaped like a wave crossing toward a small marked capital. Something real is coming. No people."),
    ("medium shot", "hero", f"{OFFICE} HERO at the rain window at night holding THE BOOK closed in both hands, calm and certain, lamp behind him. He thinks he has read this ending."),
    ("extreme close-up", "empty", "THE BOOK face-down on a dark desk, spine cracked and broken, pages splayed, cold morning light. The story failed. No people."),
    ("wide shot", "hero", f"{OFFICE} Seen from outside a rain-streaked window: HERO a small dark silhouette in the vast dark office, brass lamp lighting an open drawer with THE BOOK inside. An unfinished story, waiting."),
]


def prompt_for(who: str, scene: str) -> str:
    return f"{STYLE} SCENE: {scene}"
