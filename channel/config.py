"""Permanent channel configuration. Story content does not live here.

Originality, anti-repetition, and monetization thresholds live in
``channel/originality_policy.py``. Agents must not restate those in chat.
"""

from __future__ import annotations

import hashlib

from pydantic import BaseModel, Field

from channel.locks import SHIPPED_STYLE_LOCK


GLOBAL_VISUAL_STYLE = (
    "Simple flat 2D historical educational animation in the established "
    "What They Really Think visual identity. Clean vector-like digital "
    "illustration, simplified human anatomy, simple facial features "
    "(simple eyes, simple nose, simple mouth), clear recognizable silhouettes, "
    "flat colors, muted historical palette, minimal gradients, restrained "
    "shading, softly illustrated simplified background, uncluttered composition, "
    "expressive but restrained poses, consistent recurring character design, "
    "clean educational animation aesthetic. FILL THE ENTIRE FRAME edge to edge, "
    "no letterbox, no pillarbox, no black bars. Any on-image label, badge, sign, "
    "or diagram text must sit fully inside a 10 percent margin from every edge. "
    "Never place text flush with the top, bottom, or sides of the frame."
)

NEGATIVE_STYLE = (
    "Not photorealistic, not a photograph, not cinematic photography, not 3D, "
    "not Pixar, not anime, not manga, not watercolor, not oil painting, not "
    "hyper-detailed, not a superhero comic, not photomontage, not DSLR, not "
    "realistic skin texture. NO swastika, NO Nazi flag, NO SS runes, NO "
    "armbands, NO camps, NO gore, NO celebrity photoreal faces. No readable "
    "paragraphs of body copy, no watermarks, no captions overlaid on the frame "
    "unless the scene names a short on-screen label."
)

# Old footer kept so youtube.py can strip it from stale drafts.
LEGACY_SYNTHETIC_DISCLOSURE = (
    "Synthetic media: images and narration are generated. "
    "Not a photograph of any real person."
)

YOUTUBE_DISCLOSURE = (
    "Illustrated documentary. Stills and narration are generated. "
    "Research and story are original to this channel. "
    "Not a photograph of any real person."
)

HOST_ATTRIBUTION = (
    "Researched and written for What They Really Think from primary sources."
)

CHANNEL_ABOUT = (
    "What They Really Think makes illustrated documentaries. "
    "Each title is a new story from primary sources. "
    "Stills and voice are generated; the research and script are original "
    "to this channel. A person writes and reviews every cut.\n"
)

# New titles pick one accent so stills are not one interchangeable palette.
# Shipped slugs get an empty string (see SHIPPED_STYLE_LOCK).
VISUAL_ACCENTS = (
    "Accent this title with a cool slate-blue and cream paper palette; "
    "keep the same flat 2D construction.",
    "Accent this title with a warm lamp-amber and walnut-brown palette; "
    "keep the same flat 2D construction.",
    "Accent this title with a moss-green and parchment palette; "
    "keep the same flat 2D construction.",
    "Accent this title with a dusk-violet and pale-gold palette; "
    "keep the same flat 2D construction.",
    "Accent this title with a brick-red and ash-grey palette; "
    "keep the same flat 2D construction.",
    "Accent this title with a sea-teal and sand palette; "
    "keep the same flat 2D construction.",
)

# Kokoro only. Default stays am_liam (pacing + shipped cuts).
KOKORO_ROSTER = ("am_liam", "am_michael", "am_fenrir")

# Back-compat alias used by older imports / tests.
SYNTHETIC_DISCLOSURE = YOUTUBE_DISCLOSURE


def _stable_index(key: str, n: int) -> int:
    digest = hashlib.sha256(key.encode("utf-8")).hexdigest()
    return int(digest, 16) % n


def visual_accent_for(slug: str) -> str:
    """Per-title palette note. Empty for shipped stills that must not drift."""
    if not slug or slug in SHIPPED_STYLE_LOCK:
        return ""
    return VISUAL_ACCENTS[_stable_index(slug, len(VISUAL_ACCENTS))]


def kokoro_voice_for(slug: str) -> str:
    """Kokoro speaker for a new title. Shipped slugs stay on am_liam."""
    if not slug or slug in SHIPPED_STYLE_LOCK:
        return "am_liam"
    return KOKORO_ROSTER[_stable_index(f"{slug}:voice", len(KOKORO_ROSTER))]


class ChannelConfig(BaseModel):
    """Hardcoded style, pacing, and voice. Never a person or a plot."""

    name: str = "What They Really Think"
    title_pattern: str = "What {subject} Really {verb} About {target}"
    target_duration_seconds: int = 1380
    # Kokoro at 1.15 lands ~220 spoken wpm. 4400–5500 words plus scene
    # holds and silent cards is ~20–25 minutes. The 200 figure below is
    # only the chunker estimate for picture changes, not runtime.
    # 4–8s windows (target 6.5) keep a 23-minute cut near ~200 stills.
    narration_word_min: int = 4400
    narration_word_max: int = 5500
    narration_wpm: int = 200
    min_scene_duration: float = 4.0
    max_scene_duration: float = 8.0
    visual_change_target_seconds: float = 6.5
    default_short_enabled: bool = True
    short_word_min: int = 70
    short_word_max: int = 130
    # Free local voice. Never Edge, never ElevenLabs on this path.
    voice: str = "kokoro"
    kokoro_voice: str = "am_liam"
    kokoro_speed: float = 1.15
    kokoro_sentence_pause: float = 0.06
    kokoro_clause_pause: float = 0.02
    kokoro_pack_words: int = 1
    kokoro_scene_pause: float = 0.28
    burn_captions: bool = True
    visual_style: str = GLOBAL_VISUAL_STYLE
    negative_style: str = NEGATIVE_STYLE
    qa_revision_threshold: int = 8
    retention_block_seconds: int = 30
    banned_lecture_openers: tuple[str, ...] = Field(
        default=(
            "was born",
            "were born",
            "this video will",
            "in this video",
            "today we are going to",
            "let us begin by",
        )
    )
    banned_written_register: tuple[str, ...] = Field(
        default=(
            "furthermore",
            "consequently",
            "nevertheless",
            "it is important to note",
            "from a geopolitical perspective",
            "it can therefore be concluded",
            "during this particular period",
            "this complex relationship demonstrates",
            "throughout history",
            "in conclusion",
            "to summarize",
        )
    )


CHANNEL = ChannelConfig()
