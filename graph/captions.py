"""
Burned-in scene captions for channel videos.

Each narrated still gets its spoken line as a lower-third: heavy geometric
sans, white fill, and black stroke. No bars, rules, or fades — those read as
a crop line on the picture.

Title cards stay clean — they already *are* the type.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

_FONT_CANDIDATES = (
    "/home/levente/.local/share/fonts/Satoshi-Black.otf",
    "/home/levente/.local/share/fonts/Inter-Black.otf",
    "/usr/share/fonts/truetype/quicksand/Quicksand-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
)

_INK = (255, 255, 255, 255)
_STROKE = (0, 0, 0, 255)
_MAX_LINES = 3
_MAX_TEXT_WIDTH_FRACTION = 0.86


def _font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for path in _FONT_CANDIDATES:
        try:
            return ImageFont.truetype(path, size=max(1, size))
        except OSError:
            continue
    return ImageFont.load_default()


def wrap_caption_lines(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.ImageFont,
    max_width: int,
    max_lines: int = _MAX_LINES,
) -> list[str]:
    """Greedy word wrap; leftover words fold into the last allowed line."""
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
    kept = lines[: max_lines - 1]
    kept.append(" ".join(lines[max_lines - 1 :]))
    return kept


def _layout(
    draw: ImageDraw.ImageDraw, text: str, width: int, height: int
) -> tuple[ImageFont.ImageFont, list[str], int]:
    portrait = height > width
    size_fraction = 0.036 if portrait else 0.044
    size = round(height * size_fraction)
    min_size = max(16, round(height * 0.022))
    max_width = round(width * _MAX_TEXT_WIDTH_FRACTION)
    while size >= min_size:
        font = _font(size)
        lines = wrap_caption_lines(draw, text, font, max_width)
        fits = len(lines) <= _MAX_LINES and all(
            draw.textlength(line, font=font) <= max_width for line in lines
        )
        if fits:
            return font, lines, size
        size = max(min_size, int(size * 0.92))
        if size == min_size:
            font = _font(size)
            return font, wrap_caption_lines(draw, text, font, max_width), size
    font = _font(min_size)
    return font, wrap_caption_lines(draw, text, font, max_width), min_size


def overlay_scene_caption(src: Path, dest: Path, text: str) -> None:
    """Composite a lower-third caption onto ``src`` and write ``dest``."""
    cleaned = " ".join((text or "").split())
    src_img = Image.open(src).convert("RGB")
    if not cleaned:
        dest.parent.mkdir(parents=True, exist_ok=True)
        src_img.save(dest, "PNG")
        return

    width, height = src_img.size
    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    font, lines, size = _layout(draw, cleaned, width, height)
    if not lines:
        dest.parent.mkdir(parents=True, exist_ok=True)
        src_img.save(dest, "PNG")
        return

    boxes = [draw.textbbox((0, 0), line, font=font) for line in lines]
    line_gap = round(size * 0.22)
    text_h = sum(b[3] - b[1] for b in boxes) + line_gap * (len(lines) - 1)
    portrait = height > width
    bottom = round(height * (0.18 if portrait else 0.11))
    y = height - bottom - text_h

    stroke = max(3, size // 16)
    shadow = max(2, size // 22)
    for line, box in zip(lines, boxes, strict=True):
        text_w = box[2] - box[0]
        x = (width - text_w) // 2 - box[0]
        pos_y = y - box[1]
        draw.text(
            (x + shadow, pos_y + shadow),
            line,
            font=font,
            fill=(0, 0, 0, 140),
        )
        draw.text(
            (x, pos_y),
            line,
            font=font,
            fill=_INK,
            stroke_width=stroke,
            stroke_fill=_STROKE,
        )
        y += (box[3] - box[1]) + line_gap

    composed = Image.alpha_composite(src_img.convert("RGBA"), overlay).convert("RGB")
    dest.parent.mkdir(parents=True, exist_ok=True)
    composed.save(dest, "PNG")
