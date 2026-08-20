"""
Canonical look definition for the level-POV slideshow format.

Everything that decides *how the video looks* lives here: the hero's fixed
design, the illustration style, the generation resolution and the final output
resolution. Nodes and adapters read these constants; none of them define style
inline. Changing the channel's look is a change to this file only.

Why a locked textual hero spec
------------------------------
Image models are stateless, so the same prompt yields a different-looking
"same" character on every call. For a flat vector cartoon the practical anchor
is a *fixed, unusually specific* hero description repeated verbatim in every
scene prompt, combined with a deterministic per-shot seed. Deriving each scene
by image-to-image from a portrait reference sheet does hold the face, but it
also drags the whole frame toward the portrait's composition, which fights a
format that deliberately mixes medium character shots, wide environments, and
symbolic infographic cutaways.
"""

from __future__ import annotations

import re

# ── Resolution ────────────────────────────────────────────────────────────────
# Generation resolution. fal.ai FLUX.1 [schnell] bills per megapixel, ROUNDED
# UP to the next whole megapixel (see adapters/pricing.py). 1280x720 = 0.92MP,
# just under the 1MP floor, so it costs the same $0.003/image as a much
# smaller render would — going any lower buys nothing. This format's flat
# vector art (solid fills, thick outlines, minimal fine texture) upscales to
# 4K cleanly from 720p, so there is no visible quality trade-off.
GEN_WIDTH = 1280
GEN_HEIGHT = 720

# Final output resolution. Stills are upscaled to this on assembly; 4K uploads
# also get YouTube's better bitrate allocation, which matters for flat art with
# large uniform colour areas.
OUTPUT_WIDTH = 3840
OUTPUT_HEIGHT = 2160

FPS = 30

# ── Hero identity ─────────────────────────────────────────────────────────────
# Deliberately over-specified: every clause is a lever that keeps the character
# recognisable across independently generated frames. The oversized-head
# proportion is the single strongest identity cue in this style, so it is
# stated twice with different wording. "Sits naturally on his neck and
# shoulders, not a detached or floating balloon" was added after probing: an
# unqualified "huge head" instruction periodically produced a head so large it
# disconnected from the body entirely.
#
# Shading is deliberately allowed here (contrast the old "flat matte, no
# shading" spec): matched against real reference frames, the hero has soft
# cel-shaded gradients and a visible light-direction highlight, not a flat
# solid fill, so "no shading" was actively fighting the target look.
HERO_LOOK = (
    "A cartoon man with a noticeably oversized bald round head, roughly as wide "
    "as his shoulders, but still a head that sits naturally and proportionally "
    "on his neck and shoulders like a normal cartoon character, not a detached "
    "or floating balloon. Simple, slightly weary facial features: two small "
    "dark eyes with subtle under-eye shading, a thin eyebrow line, a small "
    "closed-line mouth, no nose detail. Soft cel-shaded skin tone with a "
    "gentle gradient and a visible light-direction highlight, not a flat "
    "single-tone fill. His body is average build, dressed for the scene "
    "(hoodie and joggers, a plain dark suit, fatigues, etc. as the scene "
    "states), rendered with the same soft shading as his head."
)

# Stored on state as the identity anchor and repeated in every scene prompt.
STYLE_DESCRIPTOR = HERO_LOOK

# Binds the hero description to the person the scene already mentions instead
# of introducing him as somebody new. Without this the description reads as a
# second character brief bolted onto the scene, and a model with good prompt
# adherence obliges by drawing two people — observed literally, with the
# oversized-head man riding on the shoulders of the "young man at a desk" the
# scene described.
HERO_BINDING = (
    "CHARACTER: the man in the scene above is this exact recurring character, "
    "not an additional person. Draw exactly one man — him — plus only the "
    "other people the scene explicitly names."
)

# ── Career progression ────────────────────────────────────────────────────────
# HERO_LOOK is deliberately identical in every prompt — that fixed anchor is
# what keeps him recognisable across independently generated frames. But the
# format's whole premise is a rank-by-rank climb, and a hero who looks
# IDENTICAL in the level-one recruit's office and the level-eight director's
# office reads as static, not as a career. The two are reconciled by keeping
# every clause of HERO_LOOK fixed (head shape, eyes, mouth, shading) and
# adding one further clause on top of it — never replacing it — that escalates
# with the story: rank markers on his clothing, and how settled his posture
# reads. The bald head rules out the usual aging tell (greying hair), so this
# leans on insignia, uniform quality and bearing instead.
#
# Four stages rather than one-per-level: real footage doesn't visibly age a
# character between two adjacent levels, and reducing the granularity is what
# keeps a change from reading as a continuity error when two consecutive
# shots are compared frame to frame.
HERO_CAREER_STAGES: tuple[str, ...] = (
    "CAREER STAGE — early career: plain, unadorned clothing with no rank "
    "insignia, badges, or decorations of any kind. His bearing is slightly "
    "unsure — shoulders a little hunched, hands often clasped or fidgeting "
    "rather than at rest.",
    "CAREER STAGE — early-mid career: his clothing now carries ONE small "
    "marker of standing appropriate to the scene (a plain badge, a single "
    "rank chevron, a nameplate) but is otherwise still modest. His bearing "
    "is more settled — standing straighter, hands more often at rest — but "
    "not yet commanding.",
    "CAREER STAGE — mid-late career: his clothing is visibly higher-rank "
    "(more insignia, a better-tailored or more senior uniform, an "
    "officer's or director's office trappings as the scene calls for). His "
    "posture is upright and deliberate, and his expression carries more "
    "visible fatigue — slightly deeper under-eye shading than his default, "
    "never a different face.",
    "CAREER STAGE — late career: his clothing signals the top of the "
    "hierarchy the scene has built (the most senior insignia, decorations, "
    "or office trappings the story has shown). He stands with settled, "
    "unhurried authority, and his under-eye shading is at its most "
    "pronounced — worn, not injured or ill.",
)


def career_stage_note(level_index: int, total_levels: int) -> str:
    """
    The ``HERO_CAREER_STAGES`` entry for a shot at ``level_index`` of
    ``total_levels`` (both 0-based / a plain count).

    Buckets by level fraction rather than a 1:1 level-to-stage mapping so a
    12-level script and an 8-level script both cover the same four stages
    end to end, rather than a longer script drifting through stages faster
    or slower than the story's own pacing.
    """
    if total_levels <= 1:
        return HERO_CAREER_STAGES[0]
    fraction = level_index / (total_levels - 1)
    stage_index = min(int(fraction * len(HERO_CAREER_STAGES)), len(HERO_CAREER_STAGES) - 1)
    return HERO_CAREER_STAGES[stage_index]


# Locking the hero's design says nothing about anyone standing next to him,
# and the model does not generalise from one to the other: given a hero spec
# and an unspecified second character, gpt-image-2 drew the hero correctly and
# rendered the official across the desk from him — and, elsewhere, his wife
# and son on the couch — as realistically-proportioned faces in a different
# idiom entirely. On screen that reads exactly as the thing this format
# cannot afford, a character swap mid-video, even though the hero himself
# never changed. The cast rule is what makes the frame one drawing.
CAST_RULE = (
    "EVERY OTHER PERSON in the frame is drawn in exactly the same cartoon "
    "construction as him: the same oversized round head roughly as wide as "
    "the shoulders, the same two small dark eyes, thin eyebrow line, small "
    "closed-line mouth and no nose detail, the same soft cel shading. They "
    "differ from him only in hair, skin tone, clothing, build and posture. "
    "No one in the frame — not a background figure, not a face on a screen, "
    "not a person in a photograph — may have a realistically-proportioned "
    "head or a detailed realistic face."
)

# ── In-image text ─────────────────────────────────────────────────────────────
# Short in-scene text is a deliberate storytelling device here (a price
# sticker, a sign, a book spine). The failure mode is not the model's spelling
# per se — asked for two or three specific strings it renders them correctly —
# it is the model *volunteering* a dozen more to fill the set dressing. Every
# invented string is another chance to misspell, and the observed typos all
# came from that filler ("POCUS PLAN REPEAT" on a mug, "Calk back!" on a
# sticky note) rather than from anything the scene actually asked for.
#
# So the rule is a budget, not a ban: render what the scene names, and leave
# the rest of the set visibly wordless.
#
# A distinct, worse failure showed up on a scene that quoted no text at all:
# asked for a bare, person-free bedroom, the model built a full-sentence
# caption banner across the frame and wrote its own scene brief onto it as
# if the request were a title card. There is nowhere in this format for that
# — the level titles are separately rendered, real title cards — so it is
# forbidden outright rather than budgeted like short in-scene signage.
TEXT_RULE = (
    "IN-IMAGE TEXT: render ONLY the specific words the scene description "
    "puts in quotes, spelled exactly as written there, large and clean. Do "
    "not invent any additional signage, labels, posters, book titles, mug "
    "slogans, sticky notes, or screen text to fill the scene — every other "
    "surface must be blank, patterned, or turned away so no other words are "
    "readable. Never render a paragraph or a wall of small body copy, and "
    "never copy any part of these instructions into the picture: this "
    "prompt is a brief, not artwork to be transcribed. Above all, NEVER add "
    "a caption, subtitle bar, or title-card-style sentence of text overlaid "
    "on top of the illustration — this is a single illustrated frame, not a "
    "slide, and it carries no text at all unless a quote above says "
    "otherwise."
)

# ── Illustration style ────────────────────────────────────────────────────────
# Detailed, moodily-lit graphic-novel / webtoon illustration — matched against
# real reference frames from "Your Life as Every Rank/Level of X" channels.
# Two earlier drafts got this wrong in opposite directions: a "moody,
# desaturated, vignetted" version had correct lighting drama but the wrong
# flatness, while a later "flat vector, bright even lighting, no shadows"
# version (matched against a *different* reference set) was too sparse and
# too evenly lit — real frames use a single visible light source (a desk
# lamp, a window, a screen) that throws warm/cool contrast and real cast
# shadows across a densely detailed environment, and short in-scene text is
# a deliberate storytelling device (a price sticker, a book spine, a comic
# sound-effect word like "SNORT!"), not something to suppress.
STYLE_BLOCK = (
    "detailed digital illustration in a graphic-novel / webtoon style, clean "
    "confident linework with soft cel-shaded gradients (not a flat solid "
    "fill), a single dominant visible light source (lamp, window, screen, or "
    "sky) that casts warm/cool colour contrast and soft directional shadows "
    "across the scene, richly detailed environment full of small concrete "
    "props and clutter relevant to the narration (specific objects, "
    "furniture, signage, screens) rather than a sparse or empty background, "
    "muted but still colourful realistic palette. NOT photorealistic, NOT "
    "anime, NOT manga, NOT a 3D render, NOT a sketch, and no "
    "realistically-proportioned human faces. " + TEXT_RULE + " No watermark, "
    "no signature."
)

# The reference format cuts between medium character shots, wide environment
# shots, extreme close-up object details, top-down flatlay shots, and
# symbolic infographic cutaways. Forcing one framing produces a monotone
# video, so the shot type is decided per scene (by the LLM, or by the local
# fallback) and only the shared framing qualities are fixed here.
#
# Explicitly bans black letterbox/pillarbox bars: the word "cinematic" (used
# in an earlier draft of this prompt) reliably made FLUX draw literal black
# bars baked into the image content itself — not an assembly-pipeline
# artifact, a real pixel-level part of the generated frame — on a
# non-trivial fraction of shots. The fix is a full-bleed instruction plus an
# explicit negative, not a video-side crop (cropping would cut into the
# subject on shots where the bars happened to be thin).
FRAMING = (
    "Full-bleed 16:9 illustration filling the entire frame edge to edge with "
    "artwork, no black bars, no letterbox bars, no pillarbox bars, no film "
    "aspect-ratio crop, generous empty space around the subject for "
    "narration captions, character or focal object small-to-medium in frame "
    "rather than a tight face close-up unless the scene specifically calls "
    "for a macro object detail shot"
)


# Words that mean a human being is in the frame. Used to catch a scene
# description that implies a person while being labelled a character-free
# shot type — see ``mentions_person``.
#
# Precision matters as much as recall here, in both directions. A miss puts an
# undescribed stranger in the frame; a false positive is just as visible, and
# costs more. "A digital clock face showing 22:00, no room, no context, just
# the number suspended in black" matched on the word *face*, so the hero
# description was appended to a deliberately empty frame — and the model
# resolved the contradiction by building a whole living room around a man on
# a couch, in the middle of a job interview. Hence the exclusions: the body
# parts below are person words only when nothing turns them into an object.
_PERSON_WORDS = re.compile(
    r"\b(?:"
    r"person|people|man|men|woman|women|boy|girl|kid|child|children|"
    r"someone|somebody|figure|figures|silhouette|silhouettes|crowd|"
    r"finger|fingers|shoulder|shoulders|"
    r"his|her|hers|he|she|him|"
    r"applicant|recruit|trainee|candidate|interviewer|instructor|officer|"
    r"agent|soldier|guard|worker|colleague|roommate|partner|stranger|"
    r"doctor|nurse|teacher|student|customer|client|boss|manager"
    r")\b"
    # "clock face", "watch face", "hour hand" — object compounds, not people.
    # "arm(s)" is left out of the list entirely rather than fenced this way:
    # the arms of a chair are as often described from a distance ("the worn
    # arms of an empty chair") as adjacently, and a scene with a real arm in
    # it says hand, shoulder, or his somewhere too.
    r"|(?<!clock )(?<!watch )(?<!cliff )(?<!rock )(?<!dial )\bfaces?\b(?![ -](?:up|down))"
    r"|(?<!clock )(?<!watch )(?<!hour )(?<!minute )(?<!second )\bhands?\b",
    re.IGNORECASE,
)

# Appended when a scene really is character-free. An implicit absence is not
# enough: asked for "notes on a notepad, a pen hovering over the page",
# gpt-image-2 supplied the person doing the hovering — a realistic stranger
# in a style nothing like the hero's.
NO_PEOPLE = (
    "NO PEOPLE IN THIS FRAME: no figures, no faces, no hands, no arms, no "
    "body parts, no reflections or photographs of people. Objects and "
    "environment only."
)


def mentions_person(scene: str) -> bool:
    """
    Whether a scene description implies a human being in the frame.

    A shot the storyboard labelled character-free can still describe one
    ("the interviewer's notepad", "a pen hovers over the page"). Dropping the
    hero from those prompts does not remove the person — it removes the only
    description of who that person is, so the model invents an off-style
    stranger. Cross-checking the prose is what makes the character-free path
    safe; the label alone is not trustworthy.
    """
    return bool(_PERSON_WORDS.search(scene))


def scene_prompt(
    scene: str,
    style_descriptor: str = "",
    include_hero: bool = True,
    career_stage: str = "",
) -> str:
    """
    Build a full image prompt for one scene.

    ``scene`` should already state its own shot type (medium shot, wide shot,
    two-character scene, symbolic graphic, ...); this function only adds the
    locked hero design and the shared illustration style around it.

    ``include_hero=False`` omits the hero block and asserts an empty frame
    instead, for shot types that have no person in them (an extreme close-up
    of an object, a top-down flatlay, a symbolic graphic). Appending a
    detailed description of a man to a prompt for an empty desk asks the
    model to reconcile two incompatible briefs, and the stronger the model
    the worse the result: a weaker model ignored the hero or half-merged him
    into the frame, while gpt-image-2 resolved the contradiction *correctly*
    by drawing the object shot AND a second man in it.

    Callers must not pass ``include_hero=False`` for a scene that mentions a
    person (see ``mentions_person``) — that combination produces a stranger,
    not an empty frame.

    ``career_stage`` (see ``career_stage_note``) is appended alongside the
    fixed hero block rather than folded into it, so the one-time identity
    anchor and the per-level thing that is allowed to move stay visibly
    separate concerns in the prompt.
    """
    look = style_descriptor.strip() or STYLE_DESCRIPTOR
    stage = career_stage.strip()
    if include_hero:
        character = f"{HERO_BINDING} {look} {CAST_RULE}"
        if stage:
            character = f"{character} {stage}"
    else:
        character = NO_PEOPLE
    return f"SCENE: {scene.strip()} {character} {FRAMING}. {STYLE_BLOCK}"


def reference_sheet_prompt(character_description: str = "") -> str:
    """Build the prompt for the hero reference sheet (identity anchor)."""
    look = character_description.strip() or HERO_LOOK
    return (
        "Character reference sheet of a single cartoon man standing facing the "
        "camera, full body, neutral pose, arms at his sides, on a plain flat "
        f"grey background. {look} {STYLE_BLOCK}"
    )


def hero_description(topic: str) -> str:
    """
    Character description for the reference sheet, given the video's topic.

    The hero is a fictional everyman, never a real or identifiable person: the
    topic only sets his clothing, never his face.
    """
    return (
        f"{HERO_LOOK} He is a fictional everyman protagonist for a video about "
        f"{topic}, not based on any real person."
    )


# Title-card layout (bold white type on a plain black frame) lives in
# graph/title_cards.py, which owns its own type sizes and proportions.
