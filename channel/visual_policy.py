"""Visual variety policy — scenes must follow the title's events, not a template."""

from __future__ import annotations

from channel.originality_policy import GENERIC_SCENE_PATTERNS

VISUAL_STYLE_LOCK = (
    "Hand-drawn 2D doodle stick-figure illustration. Muted historical palette. "
    "Solid color-block backgrounds. Not photorealistic."
)

BEHIND_THE_BUSINESS_VISUAL_STYLE_LOCK = (
    "Hand-drawn 2D doodle stick-figure business illustration. High-contrast "
    "palette. Chunky diagrams. Not photorealistic, not 3D."
)

HOW_THEY_TOOK_OVER_VISUAL_STYLE_LOCK = (
    "Hand-drawn 2D doodle stick-figure strategy illustration. Energetic "
    "high-contrast palette. Flywheels, competitor maps, timelines. Not "
    "photorealistic, not 3D, not logo-vs-logo."
)

FORBIDDEN_VISUALS = (
    "photorealistic impersonation of real people",
    "realistic fake interviews",
    "realistic fake speeches",
    "cloning the voice of the person being discussed",
    "Nazi flags / swastikas / camps / gore unless historically unavoidable and stylized",
)

__all__ = [
    "BEHIND_THE_BUSINESS_VISUAL_STYLE_LOCK",
    "FORBIDDEN_VISUALS",
    "GENERIC_SCENE_PATTERNS",
    "HOW_THEY_TOOK_OVER_VISUAL_STYLE_LOCK",
    "VISUAL_STYLE_LOCK",
]
