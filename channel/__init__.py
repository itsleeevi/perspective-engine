"""What They Really Think — title-in, documentary-out.

This package is the reusable channel engine. It does not know any specific
person. A new video starts with a title string; research, story, characters,
and scenes are data. Render still goes through the existing Kokoro + FFmpeg
path (`scripts/run_custom_video.py`).
"""

from channel.config import CHANNEL, GLOBAL_VISUAL_STYLE, NEGATIVE_STYLE

__all__ = ["CHANNEL", "GLOBAL_VISUAL_STYLE", "NEGATIVE_STYLE"]
