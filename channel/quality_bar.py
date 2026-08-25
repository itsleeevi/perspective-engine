"""Quality grammar from the best-performing shipped cuts.

Copy the GRAMMAR. Never copy the SPINES. Spec: docs/video-engine/QUALITY_BAR.md.
"""

from __future__ import annotations

import re
from collections import Counter
from channel.schema import VideoProject

QUALITY_BAR_DOC = "docs/video-engine/QUALITY_BAR.md"

# Long cuts whose *grammar* (not spine) is the production bar.
REFERENCE_LONG = (
    "What Elon Musk Really Thinks About Sam Altman",
    "How Tesla Took Over the Electric Car Industry",
    "How Costco Really Makes Money",
)

# Shorts whose *grammar* (not spine) is the production bar.
REFERENCE_SHORT = (
    "How Donald Trump Really Makes His Money",
    "What Elon Musk Really Thinks About AI",
    "How Elon Musk Really Makes His Money",
)

STAGING_QUALITY = (
    "ONE idea in the frame. ONE oversized focal object large in the middle, "
    "high contrast, never a faint mark. Unique staging this still owns. Named "
    "lighting (warm lamp, cool window, tungsten, night orange). Empty air on "
    "one side. Fill the entire frame. Recurring people keep the exact same "
    "cartoon face and ALWAYS-clothes from the lock; expression matches the "
    "action. Costume-locked extras when the beat needs a shopper or clerk. "
    "No cluttered infographic. No generic filing-table wallpaper. No logos. "
    "No readable paragraphs."
)

CHARACTER_LOCK_RECIPE = (
    "Named public figures: look up channel/character_locks.json FIRST. If "
    "present, copy visual_lock exactly and pass the hashed photo then cartoon "
    "sheet in channel/character_sheets/ as GenerateImage reference_image_paths. "
    "If new, write a lock that starts \"Same cartoon person every time, do not "
    "redesign. Copy this face:\" then face shape, jaw, eyes, hair, stubble or "
    "beard, and ALWAYS-clothes they actually wear (one outfit, no logos). End "
    "with \"Distinctive recognizable cartoon of the real person. Flat 2D "
    "vector, two-dot eyes, no skin texture, not a photograph, not photoreal. "
    "Keep this exact face in every frame.\" When two people share a frame, "
    "contrast height and face so they are not twins. Expression CHANGES with "
    "the action. Recurring extras get a costume lock (slate sweater shopper, "
    "pale blue smock clerk, orange-vest developer) — never a generic gray clerk."
)

SCENE_ACTION_RECIPE = (
    "Every still action is a cinema beat, not a slide: {SET} {who/costume} "
    "{physical verb} {one oversized focal object} {named lighting}. Accent: "
    "{corner light}, {empty margin}. Unique staging. No logos. No readable type. "
    "When the signature prop returns, paste its lock sentence: huge, oversized, "
    "high contrast, filling the middle of the frame, never faint, never a tiny "
    "version. Ban wallpaper: \"Clean business illustration of a filing table\", "
    "identical desk-and-binder loops, talking-head portraits. Rotate composition "
    "(wide / medium / close-up / OTS / establishing / object / low / high). "
    "Person-titled cuts: the named person is a recognizable cartoon in about "
    "35-42 percent of stills (lint warns below 28 percent and above 45 percent). "
    "Company-titled cuts may run empty cinematic sets with costume-locked extras. "
    "12+ locations. Unique visual verb every still. Read docs/video-engine/QUALITY_BAR.md. "
    "Copy the grammar. Never copy a reference-cut spine."
)

SHORT_RECIPE = (
    "First spoken sentence is the punch (16 words or fewer): a contradiction "
    "or a slam, not a definition. First still is that picture. 6-8 shots, a "
    "unique composition each. Hero cartoon large in frame when present. Lighting "
    "accent plus empty margin every still. Last shot is the branded CTA card. "
    "Do not spoil the long video's final button. Read docs/video-engine/QUALITY_BAR.md."
)

KID_MAP_RECIPE = (
    "title_payoff: 6-18 words, concrete, child-repeatable. Prefer two beats "
    "(\"He wanted the chair. Sam kept it.\") over a riddle. Cold open: one "
    "sourced physical contradiction in a specific place. Hook: say the_thought, "
    "then a kid map of 5-8 steps this title owns. Chapters ARE those steps "
    "(unique names from the evidence). End by saying the_thought again plus "
    "an honest limit. Copy the grammar from docs/video-engine/QUALITY_BAR.md. "
    "Never copy the spines of the reference cuts."
)

WALLPAPER_PHRASES = (
    "clean business illustration of a",
    "same construction, no logos, no readable type",
    "looking thoughtful at a desk",
    "sits at a desk looking",
    "becomes suspicious",
)

SCALE_RE = re.compile(
    r"\b(huge|oversized|giant|enormous|large in frame|filling the|"
    r"high contrast|fills the middle)\b",
    re.I,
)
FACE_BITS_RE = re.compile(r"\b(jaw|face|eyes?|hair|chin|stubble|beard|moustache|mustache)\b", re.I)
CLOTHES_RE = re.compile(
    r"\b(always|t-shirt|tshirt|sweater|suit|necktie|hoodie|jacket|smock|vest)\b", re.I
)
SAME_FACE_RE = re.compile(
    r"same cartoon|do not redesign|exact same face|copy this face", re.I
)
PERSON_TITLE_RE = re.compile(
    r"really thinks|really thought|makes his money|makes her money", re.I
)


def action_head(action: str, n: int = 8) -> str:
    words = re.findall(r"[A-Za-z0-9'_-]+", action or "")
    return " ".join(words[:n]).lower()


def is_person_title(title: str) -> bool:
    return bool(PERSON_TITLE_RE.search(title or ""))


def wallpaper_hits(action: str) -> list[str]:
    lower = (action or "").lower()
    return [phrase for phrase in WALLPAPER_PHRASES if phrase in lower]


def repeated_action_heads(
    actions: list[str],
    *,
    max_repeat: int = 12,
    max_share: float = 0.08,
) -> list[str]:
    total = len(actions) or 1
    counts = Counter(action_head(a) for a in actions if a)
    return [
        f"{head!r} repeats {n} times ({n / total:.0%} of stills)"
        for head, n in counts.most_common()
        if head and n > max_repeat and n > total * max_share
    ]


def prop_missing_scale(action: str, prop_token: str) -> bool:
    if not prop_token or prop_token not in (action or ""):
        return False
    return SCALE_RE.search(action or "") is None


def visual_lock_gaps(lock: str, *, historical_name: str = "") -> list[str]:
    text = (lock or "").strip()
    if not text:
        return ["missing visual_lock"]
    notes: list[str] = []
    if historical_name and historical_name.lower() in text.lower():
        notes.append("visual_lock contains historical_name")
    if "recognizable cartoon of the real person" not in text.lower():
        notes.append("visual_lock missing recognizable-cartoon line")
    features = {m.group(0).lower() for m in FACE_BITS_RE.finditer(text)}
    if len(features) < 2:
        notes.append("visual_lock missing face geometry (need two of face/jaw/eyes/hair)")
    if not CLOTHES_RE.search(text):
        notes.append("visual_lock missing ALWAYS-clothes")
    if not SAME_FACE_RE.search(text):
        notes.append("visual_lock missing do-not-redesign / copy-this-face")
    return notes


def short_punch_notes(first_sentence: str) -> list[str]:
    words = (first_sentence or "").strip().split()
    if not words:
        return ["Short punch sentence is empty"]
    if len(words) > 16:
        return [f"Short punch is {len(words)} words (max 16)"]
    return []


def scene_quality_notes(project: VideoProject) -> list[str]:
    notes: list[str] = []
    scenes = list(project.scenes or [])
    if not scenes:
        return notes
    actions = [s.action for s in scenes]
    notes.extend(f"wallpaper: {hit}" for action in actions for hit in wallpaper_hits(action))
    for head_note in repeated_action_heads(actions):
        notes.append(f"repeated action head: {head_note}")
    prop = ""
    if project.story and project.story.signature_prop:
        token = re.sub(r"[^A-Z0-9]+", "_", project.story.signature_prop.upper()).strip("_")
        if not token.startswith("THE_"):
            token = f"THE_{token}"
        prop = token
        for scene in scenes:
            if prop_missing_scale(scene.action, prop):
                notes.append(
                    f"{scene.scene_id}: signature prop {prop} is not huge / high-contrast / large in frame"
                )
    if is_person_title(project.title):
        hero_n = sum(1 for s in scenes if s.who == "hero")
        if hero_n < len(scenes) * 0.28:
            notes.append(
                f"person title but hero in {hero_n}/{len(scenes)} scenes "
                "(aim 35-42 percent; warn below 28 percent)"
            )
    if len(project.locations) < 12 and len(scenes) > 40:
        notes.append(f"{len(project.locations)} locations (need 12+ on a long cut)")
    return notes


def stills_quality_notes(
    actions: list[str],
    whos: list[str],
    *,
    title: str = "",
    prop_tokens: list[str] | None = None,
    short: bool = False,
) -> tuple[list[str], list[str]]:
    """Return (errors, warnings) for lint_storyboard."""
    errors: list[str] = []
    warnings: list[str] = []
    wallpaper_n = sum(1 for a in actions if wallpaper_hits(a))
    if actions and wallpaper_n > max(4, len(actions) * 0.08):
        errors.append(
            f"wallpaper: {wallpaper_n}/{len(actions)} stills use generic filing-table / "
            "desk-portrait language — write unique cinema beats"
        )
    for note in repeated_action_heads(actions):
        errors.append(f"repeated action head: {note}")
    for token in prop_tokens or []:
        missing = sum(1 for a in actions if prop_missing_scale(a, token))
        if missing:
            errors.append(
                f"prop scale: {token} in {missing} stills without huge / oversized / "
                "large in frame / high contrast"
            )
    if not short and is_person_title(title) and actions:
        hero_n = sum(1 for w in whos if w == "hero")
        if hero_n < len(actions) * 0.28:
            warnings.append(
                f"person title: hero in {hero_n}/{len(actions)} scenes — "
                "impersonate the named person as a recognizable cartoon in ~35-42%"
            )
    return errors, warnings


def prompt_markers() -> tuple[str, ...]:
    return (
        QUALITY_BAR_DOC,
        "kid map of 5-8 steps",
        "oversized focal object",
        "Same cartoon person every time",
    )
