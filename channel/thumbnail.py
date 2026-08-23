"""YouTube thumbnails: 1280×720 long, 1080×1920 Shorts. Type burned later."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from channel.shorts import SHORT_THUMB_H, SHORT_THUMB_W
from channel.youtube import THUMB_H, THUMB_W
from scripts._media import cover_crop

_FONT_CANDIDATES = (
    "/home/levente/.local/share/fonts/Satoshi-Black.otf",
    "/home/levente/.local/share/fonts/Inter-Black.otf",
    "/usr/share/fonts/truetype/quicksand/Quicksand-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
)
_INK = (255, 244, 214)
_PUNCH = (245, 197, 66)
_STROKE = (18, 12, 8)


def _font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for path in _FONT_CANDIDATES:
        try:
            return ImageFont.truetype(path, size=max(1, size))
        except OSError:
            continue
    return ImageFont.load_default()


def _wrap(draw: ImageDraw.ImageDraw, text: str, font, max_width: int, max_lines: int = 3) -> list[str]:
    words = text.split()
    if not words:
        return []
    lines: list[str] = []
    current: list[str] = []
    for word in words:
        trial = " ".join(current + [word])
        if current and draw.textlength(trial, font=font) > max_width:
            lines.append(" ".join(current))
            current = [word]
        else:
            current.append(word)
    if current:
        lines.append(" ".join(current))
    if len(lines) <= max_lines:
        return lines
    return lines[: max_lines - 1] + [" ".join(lines[max_lines - 1 :])]


def _lines_for(draw: ImageDraw.ImageDraw, text: str, font, max_width: int) -> list[str]:
    raw = (text or "").strip()
    if not raw:
        return []
    if "\n" in raw:
        return [" ".join(part.upper().split()) for part in raw.splitlines() if part.strip()]
    cleaned = " ".join(raw.upper().split())
    return _wrap(draw, cleaned, font, max_width)


def render_thumbnail_jpeg(src: Path, dest: Path, text: str) -> Path:
    """Cover-crop ``src`` to 1280×720 and burn ``text`` on the right."""
    tmp = dest.with_suffix(".work.png")
    cover_crop(src, tmp, 16, 9)
    im = Image.open(tmp).convert("RGB")
    im = im.resize((THUMB_W, THUMB_H), Image.Resampling.LANCZOS)
    draw = ImageDraw.Draw(im)
    max_width = round(THUMB_W * 0.50)
    size = 128
    font = _font(size)
    explicit = "\n" in (text or "")
    lines = _lines_for(draw, text, font, max_width)
    while size > 52 and lines and any(
        draw.textlength(ln, font=font) > max_width for ln in lines
    ):
        size = int(size * 0.92)
        font = _font(size)
        if not explicit:
            lines = _lines_for(draw, text, font, max_width)
    if lines:
        boxes = [draw.textbbox((0, 0), ln, font=font) for ln in lines]
        gap = round(size * 0.06)
        block_h = sum(b[3] - b[1] for b in boxes) + gap * (len(lines) - 1)
        x_right = THUMB_W - round(THUMB_W * 0.055)
        y = round(THUMB_H * 0.50) - block_h // 2
        y = max(round(THUMB_H * 0.14), min(y, THUMB_H - round(THUMB_H * 0.12) - block_h))
        stroke = max(5, size // 12)
        for i, (line, box) in enumerate(zip(lines, boxes, strict=True)):
            fill = _PUNCH if i == len(lines) - 1 and len(lines) > 1 else _INK
            width = box[2] - box[0]
            draw.text(
                (x_right - width - box[0], y - box[1]),
                line,
                font=font,
                fill=fill,
                stroke_width=stroke,
                stroke_fill=_STROKE,
            )
            y += (box[3] - box[1]) + gap
    dest.parent.mkdir(parents=True, exist_ok=True)
    im.save(dest, "JPEG", quality=92, optimize=True)
    tmp.unlink(missing_ok=True)
    return dest


def render_short_thumbnail_jpeg(src: Path, dest: Path, text: str) -> Path:
    """Cover-crop ``src`` to 1080×1920 and burn ``text`` in the lower third."""
    tmp = dest.with_suffix(".work.png")
    cover_crop(src, tmp, 9, 16)
    im = Image.open(tmp).convert("RGB")
    im = im.resize((SHORT_THUMB_W, SHORT_THUMB_H), Image.Resampling.LANCZOS)
    draw = ImageDraw.Draw(im)
    max_width = round(SHORT_THUMB_W * 0.86)
    size = 150
    font = _font(size)
    explicit = "\n" in (text or "")
    lines = _lines_for(draw, text, font, max_width)
    while size > 56 and lines and any(
        draw.textlength(ln, font=font) > max_width for ln in lines
    ):
        size = int(size * 0.92)
        font = _font(size)
        if not explicit:
            lines = _lines_for(draw, text, font, max_width)
    if lines:
        boxes = [draw.textbbox((0, 0), ln, font=font) for ln in lines]
        gap = round(size * 0.08)
        block_h = sum(b[3] - b[1] for b in boxes) + gap * (len(lines) - 1)
        # Sit above Shorts chrome; leave the face in the upper half clear.
        y = round(SHORT_THUMB_H * 0.72) - block_h // 2
        y = max(
            round(SHORT_THUMB_H * 0.58),
            min(y, SHORT_THUMB_H - round(SHORT_THUMB_H * 0.16) - block_h),
        )
        stroke = max(6, size // 11)
        for i, (line, box) in enumerate(zip(lines, boxes, strict=True)):
            fill = _PUNCH if i == len(lines) - 1 and len(lines) > 1 else _INK
            width = box[2] - box[0]
            x = (SHORT_THUMB_W - width) // 2 - box[0]
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
    im.save(dest, "JPEG", quality=90, optimize=True)
    tmp.unlink(missing_ok=True)
    return dest
