"""Permanent channel configuration. Story content does not live here."""

from __future__ import annotations

from pydantic import BaseModel, Field


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

SYNTHETIC_DISCLOSURE = (
    "Synthetic media: images and narration are generated. "
    "Not a photograph of any real person."
)


class ChannelConfig(BaseModel):
    """Hardcoded style, pacing, and voice. Never a person or a plot."""

    name: str = "What They Really Think"
    title_pattern: str = "What {subject} Really {verb} About {target}"
    target_duration_seconds: int = 480
    # Kokoro am_liam at 1.15 lands ~220 spoken wpm. 1600–1850 words plus
    # scene holds and silent cards is ~8 minutes. The 185 figure below is
    # only the chunker estimate for picture changes, not runtime.
    narration_word_min: int = 1600
    narration_word_max: int = 1850
    narration_wpm: int = 185
    min_scene_duration: float = 3.0
    max_scene_duration: float = 7.0
    visual_change_target_seconds: float = 4.5
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
        )
    )


CHANNEL = ChannelConfig()
