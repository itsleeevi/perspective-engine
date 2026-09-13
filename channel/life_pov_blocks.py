"""Canonical v13 prompt blocks. Section 0 of the life POV master is the source."""

from __future__ import annotations

STYLE_PEOPLE = (
    "Original detailed 2D narrative cartoon illustration, full-bleed landscape "
    "16:9, clean dark outlines, simplified expressive faces, slightly enlarged "
    "heads with complete natural bodies, muted colors, restrained cel shading, "
    "a believable era-appropriate setting, clear depth and one focal point."
)

STYLE_OBJECT = (
    "Original detailed 2D narrative cartoon illustration, full-bleed landscape "
    "16:9, clean dark outlines, carefully drawn objects, muted colors, "
    "restrained cel shading, a believable era-appropriate setting, clear depth "
    "and one focal point."
)

SKIN_LOCK_PREFIX = (
    "All visible protagonist skin is flat pure white #FFFFFF, including "
)
SKIN_LOCK_SUFFIX = (
    "; no peach, pink, tan, beige, cream, off-white, gray, blush or lighting tint."
)
SKIN_LOCK_TEMPLATE = (
    f"{SKIN_LOCK_PREFIX}[only the exposed areas actually visible in this shot]"
    f"{SKIN_LOCK_SUFFIX}"
)

ABSENCE = (
    "The recurring protagonist is completely absent, including body parts, "
    "reflections, photographs, portraits, silhouettes and shadows."
)

NO_PEOPLE = "No people or hands appear."

FINISHING = (
    "Supporting people, when present, are original fictional cartoon characters "
    "with distinct natural skin tones and age-appropriate clothing. Do not "
    "reproduce any real person's face or likeness. Show one clear frozen moment "
    "with physically natural poses and era-appropriate objects. No official club "
    "crests, logos, sponsor marks, readable text, speech bubbles, subtitles, "
    "watermark, timestamp, scene ID, player interface, caption bar, border, "
    "black silhouettes, photorealism or 3D. Fill every edge, including the "
    "bottom; no reserved subtitle space, bottom stripe, letterbox, gradient, "
    "vignette or rounded frame."
)

FINISHING_TEXT_ALLOWED_PREFIX = (
    "Supporting people, when present, are original fictional cartoon characters "
    "with distinct natural skin tones and age-appropriate clothing. Do not "
    "reproduce any real person's face or likeness. Show one clear frozen moment "
    "with physically natural poses and era-appropriate objects. The only "
    "readable text in the image is "
)
FINISHING_TEXT_ALLOWED_MID = (
    ", placed in the "
)
FINISHING_TEXT_ALLOWED_SUFFIX = (
    " area; no other readable text, lettering, numbers, speech bubbles, "
    "subtitles, watermark, timestamp or scene ID appears anywhere. No official "
    "club crests, logos, sponsor marks, player interface, caption bar, border, "
    "black silhouettes, photorealism or 3D. Fill every edge, including the "
    "bottom; no reserved subtitle space, bottom stripe, letterbox, gradient, "
    "vignette or rounded frame."
)

MASTER_FILENAME = "wealth_pov_master_v13.txt"
MASTER_VERSION = "v13"
MASTER_TITLE = (
    "LONG-FORM ILLUSTRATED CELEBRITY & LIFE POV MASTER PROMPT v13"
)

EM_DASH = "\u2014"

# Default planning band when no voice sample exists (165-175 effective WPM).
DEFAULT_SPOKEN_WORD_MIN = 5600
DEFAULT_SPOKEN_WORD_MAX = 5800
TARGET_DURATION_SECONDS = 2040
MIN_DURATION_SECONDS = 1800
MAX_DURATION_SECONDS = 2160
ORDINARY_SCENE_MIN_SECONDS = 4.0
ORDINARY_SCENE_MAX_SECONDS = 7.0
ORDINARY_SCENE_TARGET_SECONDS = 5.5
ERA_COUNT_MIN = 8
ERA_COUNT_MAX = 10
BATCH_SIZE = 20
