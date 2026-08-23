"""Visual variety policy — scenes must follow the title's events, not a template."""

from __future__ import annotations

from channel.originality_policy import GENERIC_SCENE_PATTERNS

VISUAL_STYLE_LOCK = (
    "Simple flat 2D historical illustration. Simplified faces. Vector-like shapes. "
    "Muted colors. Educational animation aesthetic. Not photorealistic."
)

FORBIDDEN_VISUALS = (
    "photorealistic impersonation of real people",
    "realistic fake interviews",
    "realistic fake speeches",
    "cloning the voice of the person being discussed",
    "Nazi flags / swastikas / camps / gore unless historically unavoidable and stylized",
)

__all__ = [
    "FORBIDDEN_VISUALS",
    "GENERIC_SCENE_PATTERNS",
    "VISUAL_STYLE_LOCK",
]
