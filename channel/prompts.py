"""Assemble image prompts from frozen style + bibles + one scene.

Agents never rewrite GLOBAL_VISUAL_STYLE. They only fill action / composition.
Historical personal names stay out of the image prompt (safety); identity is
the character bible's visual_lock.
"""

from __future__ import annotations

import re

from channel.bibles import format_all_characters, format_all_locations, visual_lock
from channel.config import config_for_project, visual_accent_for
from channel.schema import Scene, VideoProject


# Spoken VO should name these. Image models should not — they print logos.
_IMAGE_BRANDS = (
    "OpenAI",
    "ChatGPT",
    "SpaceX",
    "Tesla",
    "xAI",
    "Grok",
    "Colossus",
    "Microsoft",
    "Google",
    "DeepMind",
    "Amazon",
    "Blue Origin",
    "New Glenn",
    "New Shepard",
    "Starlink",
    "Starship",
    "Project Kuiper",
    "Amazon Leo",
    "Kuiper",
    "NASA",
    "Falcon",
)


def strip_image_brands(text: str) -> str:
    """Company and product names stay out of image prompts."""
    out = text
    for name in sorted(_IMAGE_BRANDS, key=len, reverse=True):
        out = re.sub(rf"\b{re.escape(name)}\b", "", out, flags=re.I)
    return re.sub(r"\s{2,}", " ", out).strip()


def strip_character_names(text: str, project: VideoProject) -> str:
    """Historical personal names stay out of image prompts (safety)."""
    names: list[str] = []
    for person in project.characters.values():
        raw = (person.historical_name or "").strip()
        if len(raw) >= 4:
            names.append(raw)
        for part in raw.split():
            if len(part) >= 4:
                names.append(part)
    names.sort(key=len, reverse=True)
    out = text
    seen: set[str] = set()
    for name in names:
        key = name.lower()
        if key in seen:
            continue
        seen.add(key)
        out = re.sub(rf"\b{re.escape(name)}\b", "", out, flags=re.I)
    return re.sub(r"\s{2,}", " ", out).strip()


def assemble_image_prompt(
    project: VideoProject,
    scene: Scene,
    *,
    aspect: str = "16:9",
) -> str:
    chars = []
    if scene.who != "empty":
        for cid in scene.characters:
            person = project.characters.get(cid)
            if person:
                chars.append(visual_lock(person))
        if not chars:
            chars.append(format_all_characters(project))
    loc = ""
    if scene.location and scene.location in project.locations:
        from channel.bibles import location_lock

        loc = location_lock(project.locations[scene.location])
    elif format_all_locations(project):
        loc = format_all_locations(project)

    who_rule = {
        "empty": "STRICTLY NO people, NO faces, NO hands.",
        "hero": "Only the subject character unless the action names someone else.",
        "crowd": "Generic extras in the same flat-vector construction. No photoreal faces.",
    }.get(scene.who, "Draw only the named characters.")

    label = ""
    if scene.on_screen_text:
        label = (
            f" On-screen label (only these words, large and clean): "
            f'"{scene.on_screen_text}".'
        )

    aspect_line = (
        "Vertical 9:16 frame, subject large in the upper two thirds."
        if aspect == "9:16"
        else "Horizontal 16:9 frame."
    )

    cfg = config_for_project(project)
    assembled = " ".join(
        p
        for p in (
            cfg.visual_style,
            visual_accent_for(project.slug, project.channel_mode),
            aspect_line,
            cfg.negative_style,
            " ".join(chars),
            loc,
            who_rule,
            f"SHOT: {scene.composition}.",
            f"ACTION: {scene.action}",
            label,
        )
        if p
    )
    return strip_image_brands(
        strip_character_names(strip_project_brands(assembled, project), project)
    )


def strip_project_brands(text: str, project: VideoProject) -> str:
    """Spoken company names stay out of image prompts."""
    extras: list[str] = []
    if project.analysis.subject:
        extras.append(project.analysis.subject)
    if project.analysis.company:
        extras.append(project.analysis.company)
    if project.business and project.business.company:
        extras.append(project.business.company)
    if project.takeover and project.takeover.subject:
        extras.append(project.takeover.subject)
    out = text
    for name in sorted({n for n in extras if len(n) >= 4}, key=len, reverse=True):
        out = re.sub(rf"\b{re.escape(name)}\b", "", out, flags=re.I)
    return re.sub(r"\s{2,}", " ", out).strip()
