"""
Burned-in scene captions for channel videos.

Each narrated still gets its spoken line as a lower-third: heavy geometric
sans, white fill, and black stroke. No bars, rules, or fades — those read as
a crop line on the picture.

Title cards stay clean — they already *are* the type.

Portrait (Shorts) captions sit in the YouTube safe band: above the like /
title / music chrome, inside the side rails. Landscape captions stay in the
lower third with real side margins so the last wrapped line is never sheared.
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
_MAX_LINES_LANDSCAPE = 3
_MAX_LINES_PORTRAIT = 4
# YouTube Shorts chrome covers the bottom ~28–32% and a right rail.
_BOTTOM_FRAC_PORTRAIT = 0.32
_BOTTOM_FRAC_LANDSCAPE = 0.12
_WIDTH_FRAC_PORTRAIT = 0.70
_WIDTH_FRAC_LANDSCAPE = 0.76


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
    max_lines: int = _MAX_LINES_LANDSCAPE,
) -> list[str]:
    """Greedy word wrap. Overflow becomes a new line, then an ellipsis."""
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
        return [_fit_line(draw, line, font, max_width) for line in lines]
    kept = lines[: max_lines - 1]
    leftover = " ".join(lines[max_lines - 1 :])
    kept.append(_fit_line(draw, leftover, font, max_width, ellipsis=True))
    return kept


def _fit_line(
    draw: ImageDraw.ImageDraw,
    line: str,
    font: ImageFont.ImageFont,
    max_width: int,
    *,
    ellipsis: bool = False,
) -> str:
    """Guarantee one drawn line never exceeds max_width (stroke lives outside)."""
    if draw.textlength(line, font=font) <= max_width:
        return line
    words = line.split()
    if not words:
        return line
    suffix = "…" if ellipsis else ""
    kept: list[str] = []
    for word in words:
        trial = " ".join(kept + [word]) + suffix
        if kept and draw.textlength(trial, font=font) > max_width:
            break
        kept.append(word)
    if not kept:
        # Single overlong token: walk characters.
        token = words[0]
        cut = token
        while cut and draw.textlength(cut + suffix, font=font) > max_width:
            cut = cut[:-1]
        return (cut + suffix) if cut else suffix
    out = " ".join(kept) + suffix
    while out and draw.textlength(out, font=font) > max_width:
        out = out[:-1]
    return out


def _layout(
    draw: ImageDraw.ImageDraw, text: str, width: int, height: int
) -> tuple[ImageFont.ImageFont, list[str], int]:
    portrait = height > width
    max_lines = _MAX_LINES_PORTRAIT if portrait else _MAX_LINES_LANDSCAPE
    size_fraction = 0.032 if portrait else 0.042
    size = round(height * size_fraction)
    min_size = max(14, round(height * (0.018 if portrait else 0.020)))
    width_frac = _WIDTH_FRAC_PORTRAIT if portrait else _WIDTH_FRAC_LANDSCAPE
    max_width = round(width * width_frac)
    while size >= min_size:
        font = _font(size)
        stroke = max(3, size // 16)
        usable = max(32, max_width - 2 * stroke)
        lines = wrap_caption_lines(draw, text, font, usable, max_lines=max_lines)
        fits = len(lines) <= max_lines and all(
            draw.textlength(line, font=font) <= usable for line in lines
        )
        if fits:
            return font, lines, size
        size = max(min_size, int(size * 0.90))
        if size == min_size:
            font = _font(size)
            stroke = max(3, size // 16)
            usable = max(32, max_width - 2 * stroke)
            return font, wrap_caption_lines(
                draw, text, font, usable, max_lines=max_lines
            ), size
    font = _font(min_size)
    stroke = max(3, min_size // 16)
    usable = max(32, max_width - 2 * stroke)
    return font, wrap_caption_lines(
        draw, text, font, usable, max_lines=max_lines
    ), min_size


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
    bottom = round(
        height * (_BOTTOM_FRAC_PORTRAIT if portrait else _BOTTOM_FRAC_LANDSCAPE)
    )
    y = height - bottom - text_h
    # Never let a tall wrap climb into the top third (faces / thumbs).
    min_y = round(height * (0.48 if portrait else 0.62))
    if y < min_y:
        y = min_y

    stroke = max(3, size // 16)
    shadow = max(2, size // 22)
    for line, box in zip(lines, boxes, strict=True):
        text_w = box[2] - box[0]
        x = (width - text_w) // 2 - box[0]
        x = max(stroke + 2, min(x, width - text_w - stroke - 2))
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
