"""Character and location bibles → prompt fragments. No names of specific people."""

from __future__ import annotations

from channel.schema import Character, Location, VideoProject


def visual_lock(character: Character) -> str:
    if character.visual_lock.strip():
        return character.visual_lock.strip()
    bits = [
        f"CHARACTER {character.id} (same cartoon person every time, do not redesign)",
        character.face,
        character.hair,
        character.facial_hair,
        character.body,
        character.default_clothing,
        ", ".join(character.recognition_features),
        "flat 2D vector, simple facial features, NOT photoreal, NOT a celebrity likeness",
    ]
    return ". ".join(b for b in bits if b)


def location_lock(location: Location) -> str:
    pal = f" Palette: {', '.join(location.palette)}." if location.palette else ""
    return f"LOCATION {location.id} (same set): {location.description}.{pal}"


def format_all_characters(project: VideoProject) -> str:
    if not project.characters:
        return ""
    return " ".join(visual_lock(c) for c in project.characters.values())


def format_all_locations(project: VideoProject) -> str:
    if not project.locations:
        return ""
    return " ".join(location_lock(loc) for loc in project.locations.values())


def token_for_location(location_id: str) -> str:
    return location_id.upper().replace("-", "_")
