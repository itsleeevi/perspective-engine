"""Permanent channel configuration. Story content does not live here.

Originality, anti-repetition, and monetization thresholds live in
``channel/originality_policy.py``. Agents must not restate those in chat.
"""

from __future__ import annotations

import hashlib

from pydantic import BaseModel, Field

from channel.locks import SHIPPED_STYLE_LOCK
from channel.modes import ChannelMode, parse_mode


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

BEHIND_THE_BUSINESS_VISUAL_STYLE = (
    "Clean flat 2D business documentary illustration in the established "
    "Behind The Business channel identity. Modern vector-like shapes, simple "
    "readable characters, simplified products and environments, crisp diagrams, "
    "subtle depth, limited shading, clean high-contrast palette, uncluttered "
    "compositions, clear information hierarchy, visually intuitive financial "
    "flows and business systems, consistent recurring locations and company "
    "elements. Educational but cinematic in composition. FILL THE ENTIRE FRAME "
    "edge to edge, no letterbox, no pillarbox, no black bars. Any on-image "
    "label, badge, sign, or diagram text must sit fully inside a 10 percent "
    "margin from every edge. Never place text flush with the top, bottom, or "
    "sides of the frame. Not photorealistic, not 3D, not anime, not painterly, "
    "not generic stock imagery."
)

BEHIND_THE_BUSINESS_NEGATIVE_STYLE = (
    NEGATIVE_STYLE + " Not a 3D corporate animation, not a stock-photo slideshow, "
    "not a Bloomberg terminal wall of numbers, not a photoreal product shot."
)

BTB_YOUTUBE_DISCLOSURE = (
    "Illustrated documentary. Stills and narration are generated. "
    "Research and story are original to this channel. "
    "Educational business analysis, not investment advice. "
    "Not a photograph of any real person."
)

BTB_HOST_ATTRIBUTION = (
    "Researched and written for Behind The Business from company filings "
    "and primary sources."
)

BTB_CHANNEL_ABOUT = (
    "Behind The Business explains the hidden systems, economics, and "
    "decisions behind companies people already use. "
    "Stills and voice are generated; the research and script are original "
    "to this channel. A person writes and reviews every cut. "
    "Not investment advice.\n"
)

# Modern high-contrast accents. No company names. Shipped WTRT slugs stay locked.
BTB_VISUAL_ACCENTS = (
    "Accent this title with a navy, ice-white, and sharp teal palette; "
    "keep the same clean flat 2D construction.",
    "Accent this title with a graphite, paper-white, and signal-orange palette; "
    "keep the same clean flat 2D construction.",
    "Accent this title with a deep ink, silver, and electric-blue palette; "
    "keep the same clean flat 2D construction.",
    "Accent this title with a charcoal, cream, and mint-green palette; "
    "keep the same clean flat 2D construction.",
    "Accent this title with a midnight, pale-sand, and coral palette; "
    "keep the same clean flat 2D construction.",
    "Accent this title with a slate, bright-white, and gold-line palette; "
    "keep the same clean flat 2D construction.",
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


def visual_accent_for(slug: str, mode: ChannelMode | str | None = None) -> str:
    """Per-title palette note. Empty for shipped stills that must not drift."""
    if not slug or slug in SHIPPED_STYLE_LOCK:
        return ""
    accents = (
        BTB_VISUAL_ACCENTS
        if parse_mode(mode) is ChannelMode.behind_the_business
        else VISUAL_ACCENTS
    )
    return accents[_stable_index(slug, len(accents))]


def kokoro_voice_for(slug: str) -> str:
    """Kokoro speaker for a new title. Shipped slugs stay on am_liam."""
    if not slug or slug in SHIPPED_STYLE_LOCK:
        return "am_liam"
    return KOKORO_ROSTER[_stable_index(f"{slug}:voice", len(KOKORO_ROSTER))]


class ChannelConfig(BaseModel):
    """Hardcoded style, pacing, and voice. Never a person or a plot."""

    mode: ChannelMode = ChannelMode.what_they_really_think
    name: str = "What They Really Think"
    title_pattern: str = "What {subject} Really {verb} About {target}"
    target_duration_seconds: int = 1380
    min_duration_seconds: int = 1200
    max_duration_seconds: int = 1500
    spoken_wpm_min: int = 145
    spoken_wpm_max: int = 155
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
    short_word_min: int = 60
    short_word_max: int = 135
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
    title_payoff_max_words: int = 22
    chapter_count_min: int = 4
    chapter_count_max: int = 6
    host_attribution: str = HOST_ATTRIBUTION
    channel_about: str = CHANNEL_ABOUT
    youtube_disclosure: str = YOUTUBE_DISCLOSURE
    videos_index: str = "docs/videos/README.md"
    playbook: str = "docs/custom-videos.md"
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

BEHIND_THE_BUSINESS = ChannelConfig(
    mode=ChannelMode.behind_the_business,
    name="Behind The Business",
    title_pattern="How {company} Really Makes Money",
    target_duration_seconds=1320,
    min_duration_seconds=1200,
    max_duration_seconds=1500,
    spoken_wpm_min=145,
    spoken_wpm_max=155,
    narration_word_min=3000,
    narration_word_max=3750,
    narration_wpm=150,
    min_scene_duration=4.0,
    max_scene_duration=8.0,
    visual_change_target_seconds=6.0,
    default_short_enabled=True,
    short_word_min=75,
    short_word_max=140,
    voice="kokoro",
    kokoro_voice="am_liam",
    kokoro_speed=0.92,
    visual_style=BEHIND_THE_BUSINESS_VISUAL_STYLE,
    negative_style=BEHIND_THE_BUSINESS_NEGATIVE_STYLE,
    title_payoff_max_words=28,
    chapter_count_min=5,
    chapter_count_max=8,
    host_attribution=BTB_HOST_ATTRIBUTION,
    channel_about=BTB_CHANNEL_ABOUT,
    youtube_disclosure=BTB_YOUTUBE_DISCLOSURE,
    videos_index="docs/business/README.md",
    playbook="docs/behind-the-business.md",
    banned_lecture_openers=(
        "was born",
        "were born",
        "was founded",
        "were founded",
        "this video will",
        "in this video",
        "today we are going to",
        "let us begin by",
        "the company was founded",
    ),
)

CHANNEL_CONFIGS: dict[ChannelMode, ChannelConfig] = {
    ChannelMode.what_they_really_think: CHANNEL,
    ChannelMode.behind_the_business: BEHIND_THE_BUSINESS,
}


def config_for(mode: ChannelMode | str | None = None) -> ChannelConfig:
    """Return the frozen config for a channel. Default is What They Really Think."""
    return CHANNEL_CONFIGS[parse_mode(mode)]


def config_for_project(project: object) -> ChannelConfig:
    return config_for(getattr(project, "channel_mode", None))
