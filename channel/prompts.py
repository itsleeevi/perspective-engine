"""Assemble image prompts from frozen style + bibles + one scene.

Agents never rewrite GLOBAL_VISUAL_STYLE. They only fill action / composition.
Historical personal names stay out of the image prompt (safety); identity is
the character bible's visual_lock.
"""

from __future__ import annotations

import re

from channel.bibles import format_all_characters, format_all_locations, visual_lock
from channel.config import CHANNEL
from channel.schema import Scene, VideoProject


def strip_character_names(text: str, project: VideoProject) -> str:
    """Historical personal names stay out of image prompts (safety)."""
    names: list[str] = []
    for person in project.characters.values():
        for raw in (person.historical_name, person.display_name):
            raw = raw.strip()
            if len(raw) >= 4:
                names.append(raw)
            parts = raw.split()
            if len(parts) >= 2 and len(parts[-1]) >= 4:
                names.append(parts[-1])
    names.sort(key=len, reverse=True)
    out = text
    for name in names:
        out = re.sub(re.escape(name), "", out, flags=re.I)
    return re.sub(r"\s{2,}", " ", out).strip()


def assemble_image_prompt(
    project: VideoProject,
    scene: Scene,
    *,
    aspect: str = "16:9",
) -> str:
    chars = []
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

    assembled = " ".join(
        p
        for p in (
            CHANNEL.visual_style,
            aspect_line,
            CHANNEL.negative_style,
            " ".join(chars),
            loc,
            who_rule,
            f"SHOT: {scene.composition}.",
            f"ACTION: {scene.action}",
            label,
        )
        if p
    )
    return strip_character_names(assembled, project)
