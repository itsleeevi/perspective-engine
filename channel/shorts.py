"""YouTube Shorts: spoken CTA end card and 9:16 thumbnail.

Every Short ends on the same line — watch the full video, link in the
description — spoken by Kokoro and shown on a branded card. Compile writes
a 9:16 thumbnail job; type is burned later, same as the 16:9 long thumb.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from channel.config import CHANNEL
from channel.paths import ROOT, jobs_path
from channel.prompts import strip_character_names
from channel.schema import Scene, ScenePurpose, VideoProject

SHORT_CTA = "Watch the full video. The link is in the description."
SHORT_THUMB_W, SHORT_THUMB_H = 1080, 1920

_TRAILING_CTA = re.compile(
    r"\s*(?:"
    r"(?:The\s+)?full story is on this channel\.?|"
    r"Watch the full video\.?(?:\s+The link is in the description\.?)?|"
    r"The link is in the description\.?|"
    r"Link(?:s)? in the description\.?"
    r")\s*$",
    re.I,
)

_FONT_CANDIDATES = (
    "/home/levente/.local/share/fonts/Satoshi-Black.otf",
    "/home/levente/.local/share/fonts/Inter-Black.otf",
    "/usr/share/fonts/truetype/quicksand/Quicksand-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
)
_BG = (11, 18, 36)
_INK = (255, 244, 214)
_PUNCH = (245, 197, 66)
_STROKE = (18, 12, 8)


def is_short_cta(text: str) -> bool:
    lowered = " ".join((text or "").lower().split())
    return "watch the full video" in lowered and "description" in lowered


def strip_short_cta(text: str) -> str:
    out = (text or "").strip()
    while True:
        nxt = _TRAILING_CTA.sub("", out).strip()
        if nxt == out:
            return nxt
        out = nxt


def ensure_short_cta(text: str) -> str:
    body = strip_short_cta(text)
    return f"{body} {SHORT_CTA}".strip() if body else SHORT_CTA


def short_cta_scene() -> Scene:
    return Scene(
        scene_id="short_cta",
        narration=SHORT_CTA,
        purpose=ScenePurpose.next_video_bridge,
        visual_type="end_card",
        action="End card. Dark navy field. No people. Type added in assemble.",
        composition="title card",
        who="empty",
        camera_motion="static",
    )


def attach_short_cta_scene(scenes: list[Scene], chunks: list[str]) -> list[Scene]:
    """Make the last short scene the branded CTA when the last chunk is."""
    scenes = list(scenes)
    if not chunks or not is_short_cta(chunks[-1]):
        return scenes
    if scenes and is_short_cta(scenes[-1].narration):
        scenes[-1] = short_cta_scene()
        return scenes
    scenes.append(short_cta_scene())
    return scenes


def _font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for path in _FONT_CANDIDATES:
        try:
            return ImageFont.truetype(path, size=max(1, size))
        except OSError:
            continue
    return ImageFont.load_default()


def render_short_end_card(
    dest: Path,
    *,
    width: int = SHORT_THUMB_W,
    height: int = SHORT_THUMB_H,
) -> Path:
    """9:16 navy card: WATCH THE FULL VIDEO / LINK IN THE DESCRIPTION."""
    im = Image.new("RGB", (width, height), _BG)
    draw = ImageDraw.Draw(im)
    lines = (
        ("WATCH THE", _INK),
        ("FULL VIDEO", _INK),
        ("LINK IN THE", _PUNCH),
        ("DESCRIPTION", _PUNCH),
    )
    size = round(height * 0.075)
    font = _font(size)
    max_width = round(width * 0.84)
    while size > 28 and any(
        draw.textlength(line, font=font) > max_width for line, _ in lines
    ):
        size = int(size * 0.92)
        font = _font(size)
    boxes = [draw.textbbox((0, 0), line, font=font) for line, _ in lines]
    gap = round(size * 0.18)
    block_h = sum(b[3] - b[1] for b in boxes) + gap * (len(lines) - 1)
    y = (height - block_h) // 2
    stroke = max(6, size // 11)
    for (line, fill), box in zip(lines, boxes, strict=True):
        w = box[2] - box[0]
        x = (width - w) // 2 - box[0]
        draw.text(
            (x, y - box[1]),
            line,
            font=font,
            fill=fill,
            stroke_width=stroke,
            stroke_fill=_STROKE,
        )
        y += (box[3] - box[1]) + gap
    dest.parent.mkdir(parents=True, exist_ok=True)
    im.save(dest, "PNG")
    return dest


def short_thumbnail_prompt(project: VideoProject) -> str:
    from channel.bibles import visual_lock

    meta = project.metadata
    concept = (meta.thumbnail_concept if meta else "") or (
        "Tight chest-up of the subject. Face fills the upper half. "
        "Empty lower third for type."
    )
    subject = next((c for c in project.characters.values() if c.is_subject), None)
    lock = visual_lock(subject) if subject else ""
    prop = ""
    if project.story and project.story.signature_prop:
        prop = f" Signature object: {project.story.signature_prop}."
    assembled = " ".join(
        p
        for p in (
            CHANNEL.visual_style,
            "Vertical 9:16 YouTube Shorts thumbnail. TIGHT crop, chest-up or "
            "closer. The subject's FACE fills the upper half of the frame and "
            "is the brightest thing in the picture. Dramatic single-source "
            "light, bold colour contrast, clean simple backdrop. Subtle natural "
            "expression, not a grimace, not a shout. Empty dark lower third of "
            "the frame for type added later. No tiny figures, no wide "
            "establishing shot, no clutter.",
            CHANNEL.negative_style,
            "NO readable text, NO letters, NO captions, NO title card, "
            "NO watermark. Type will be added later.",
            lock,
            concept,
            prop,
        )
        if p
    )
    return strip_character_names(assembled, project)


def write_short_thumbnail_job(project: VideoProject, *, root: Path | None = None) -> Path:
    slug = project.slug
    from channel.youtube import youtube_stem

    stem = youtube_stem(slug)
    meta = project.metadata
    text = (meta.thumbnail_text if meta else "") or "THE REAL ANSWER"
    job = {
        "id": "short_thumb",
        "filename": f"{slug}_short_thumbnail.png",
        "aspect": "9:16",
        "overlay_text": text,
        "output_jpeg": f"assets/youtube/{stem}_short_thumbnail_1080x1920.jpg",
        "prompt": short_thumbnail_prompt(project),
    }
    out = jobs_path(f"{slug}_short_thumbnail_", root)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"jobs": [job]}, indent=2) + "\n", encoding="utf-8")
    return out


def find_short_thumbnail_still(slug: str, *, root: Path | None = None) -> Path | None:
    base = root or ROOT
    names = (f"{slug}_short_thumbnail.png", f"{slug}_shorts_thumb.png")
    cursor = (
        Path.home()
        / ".cursor"
        / "projects"
        / str(base).strip("/").replace("/", "-")
        / "assets"
    )
    dirs = (
        base / "assets" / "grok_thumbs",
        base / "assets" / "youtube",
        cursor,
    )
    for folder in dirs:
        for name in names:
            path = folder / name
            if path.is_file():
                return path
    return None
