"""What They Really Think — title-in, documentary-out.

This package is the reusable channel engine. It does not know any specific
person. A new video starts with a title string; research, story, characters,
and scenes are data. Render still goes through the existing Kokoro + FFmpeg
path (`scripts/run_custom_video.py`).
"""

from channel.config import (
    BEHIND_THE_BUSINESS,
    BEHIND_THE_BUSINESS_VISUAL_STYLE,
    CHANNEL,
    GLOBAL_VISUAL_STYLE,
    HOW_THEY_TOOK_OVER,
    HOW_THEY_TOOK_OVER_VISUAL_STYLE,
    NEGATIVE_STYLE,
)

__all__ = [
    "BEHIND_THE_BUSINESS",
    "BEHIND_THE_BUSINESS_VISUAL_STYLE",
    "CHANNEL",
    "GLOBAL_VISUAL_STYLE",
    "HOW_THEY_TOOK_OVER",
    "HOW_THEY_TOOK_OVER_VISUAL_STYLE",
    "NEGATIVE_STYLE",
]
