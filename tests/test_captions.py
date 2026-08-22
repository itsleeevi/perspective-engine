"""Smoke tests for burned-in scene captions."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

from graph.captions import overlay_scene_caption, wrap_caption_lines, _font
from graph.title_cards import render_title_card


def test_wrap_breaks_long_line():
    img = Image.new("RGB", (640, 360), (20, 20, 20))
    draw = ImageDraw.Draw(img)
    lines = wrap_caption_lines(
        draw,
        "He thought God was the order of the universe, not a person who listens.",
        _font(28),
        max_width=400,
    )
    assert len(lines) >= 2
    assert all(lines)


def test_overlay_writes_requested_size(tmp_path: Path):
    src = tmp_path / "still.png"
    Image.new("RGB", (640, 360), (80, 90, 70)).save(src)
    dest = tmp_path / "out.png"
    overlay_scene_caption(
        src, dest, "He believes in Spinoza's God, who reveals himself in the world."
    )
    with Image.open(dest) as img:
        assert img.size == (640, 360)
        # Caption lives in the lower third; it must change those pixels.
        bottom = img.crop((0, 240, 640, 360))
        assert bottom.getextrema() != ((80, 80), (90, 90), (70, 70))


def test_empty_caption_is_a_copy(tmp_path: Path):
    src = tmp_path / "still.png"
    Image.new("RGB", (320, 180), (10, 20, 30)).save(src)
    dest = tmp_path / "out.png"
    overlay_scene_caption(src, dest, "   ")
    with Image.open(dest) as img:
        assert img.getpixel((0, 0)) == (10, 20, 30)


def test_overlay_has_no_gold_rule(tmp_path: Path):
    src = tmp_path / "still.png"
    Image.new("RGB", (640, 360), (40, 40, 40)).save(src)
    dest = tmp_path / "out.png"
    overlay_scene_caption(src, dest, "A cardinal in Boston has just said relativity.")
    with Image.open(dest) as img:
        gold = 0
        pix = img.load()
        width, height = img.size
        for y in range(height):
            for x in range(width):
                r, g, b = pix[x, y]
                if r > 180 and 150 < g < 230 and b < 160 and (g - b) > 40:
                    gold += 1
        assert gold == 0


def test_title_cards_stay_separate_from_captions():
    # Contract: chapter cards are their own graphic; captions are for stills.
    url = render_title_card("[TITLE] (silent) The Telegram", width=320, height=180)
    assert "title_cards" in url
