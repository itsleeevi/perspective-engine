"""
Local title-card stills for level transitions.

Renders the level number and name as bold white type on a plain black frame,
without calling an image model, so every level break is free and pixel-exact.

This deliberately replaces an earlier "classified dossier folder" graphic.
The reference videos this format follows cut to a full-bleed black card with
nothing on it but the level name — the break reads as a hard beat in the
story, and a plain card keeps that beat generic enough to fit any topic
(a dossier motif only ever suited the espionage ones).

Type sizes are expressed as fractions of frame height, so the same card
renders identically at 720p or 4K.
"""

from __future__ import annotations

import hashlib
import io
import re

from PIL import Image, ImageDraw, ImageFont

from graph import style
from graph.assets import save_asset
from graph.script_fixture import title_card_lines

# Heavy geometric sans first (closest to the reference cards), falling back
# through progressively more common faces so a machine without the display
# fonts installed still renders a correct card rather than crashing.
_FONT_CANDIDATES = (
    "/home/levente/.local/share/fonts/Satoshi-Black.otf",
    "/home/levente/.local/share/fonts/Inter-Black.otf",
    "/usr/share/fonts/truetype/quicksand/Quicksand-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
)

_BG = (0, 0, 0)
_INK = (255, 255, 255)

# Cap height of one line as a fraction of frame height, and the gap between
# the two lines as a fraction of the type size.
_LINE_HEIGHT_FRACTION = 0.135
_LINE_GAP_FRACTION = 0.34
# Longer level names are stepped down so they never run past the safe margin.
_MAX_TEXT_WIDTH_FRACTION = 0.82


def _font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for path in _FONT_CANDIDATES:
        try:
            return ImageFont.truetype(path, size=max(1, size))
        except OSError:
            continue
    return ImageFont.load_default()


def _fitted_font(
    draw: ImageDraw.ImageDraw, text: str, size: int, max_width: int
) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Largest font at or below ``size`` that keeps ``text`` inside the margin."""
    font = _font(size)
    while size > 8 and draw.textlength(text, font=font) > max_width:
        size = int(size * 0.94)
        font = _font(size)
    return font


def render_title_card(
    title_beat: str,
    width: int = style.OUTPUT_WIDTH,
    height: int = style.OUTPUT_HEIGHT,
) -> str:
    """
    Render a level title card and return a ``file://`` asset URL.

    ``title_beat`` may include the ``[TITLE]`` prefix. "Level One: The
    Applicant" is set as two centred lines, "Level One:" above "The
    Applicant"; a beat with no colon is set as a single line.
    """
    line1, line2 = title_card_lines(title_beat)
    lines = [ln for ln in (line1.strip(), line2.strip()) if ln]
    if not lines:
        lines = ["Level"]

    slug_src = f"{line1}|{line2}|{width}x{height}".lower()
    slug = re.sub(r"[^a-z0-9]+", "_", slug_src).strip("_")[:50]
    digest = hashlib.sha1(slug_src.encode("utf-8")).hexdigest()[:8]

    img = Image.new("RGB", (width, height), color=_BG)
    draw = ImageDraw.Draw(img)

    size = round(height * _LINE_HEIGHT_FRACTION)
    max_width = round(width * _MAX_TEXT_WIDTH_FRACTION)
    fonts = [_fitted_font(draw, text, size, max_width) for text in lines]

    boxes = [draw.textbbox((0, 0), t, font=f) for t, f in zip(lines, fonts, strict=True)]
    gap = round(size * _LINE_GAP_FRACTION)
    total_h = sum(b[3] - b[1] for b in boxes) + gap * (len(lines) - 1)

    y = (height - total_h) // 2
    for text, font, box in zip(lines, fonts, boxes, strict=True):
        text_w = box[2] - box[0]
        draw.text(
            ((width - text_w) // 2 - box[0], y - box[1]), text, fill=_INK, font=font
        )
        y += (box[3] - box[1]) + gap

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return save_asset(f"title_cards/{slug}_{digest}.png", buf.getvalue())
