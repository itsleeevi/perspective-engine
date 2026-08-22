"""Cover-crop must never shear top-of-frame labels."""

from __future__ import annotations

from pathlib import Path

from PIL import Image

from scripts._media import cover_crop


def test_16x9_crop_keeps_the_top_band(tmp_path: Path):
    # Grok 3:2 stills: 1536x1024 → 16:9 drops 160px of height.
    src = tmp_path / "still.png"
    im = Image.new("RGB", (1536, 1024), (20, 40, 60))
    for y in range(80):
        for x in range(1536):
            im.putpixel((x, y), (255, 0, 0))
    im.save(src)
    dest = tmp_path / "out.png"
    cover_crop(src, dest, 16, 9)
    out = Image.open(dest)
    assert out.size[0] / out.size[1] == 16 / 9 or abs(out.size[0] / out.size[1] - 16 / 9) < 0.01
    # The red top band must still be at y=0 after crop.
    assert out.getpixel((10, 0)) == (255, 0, 0)
    assert out.getpixel((10, 40)) == (255, 0, 0)


def test_wide_image_keeps_center(tmp_path: Path):
    src = tmp_path / "still.png"
    im = Image.new("RGB", (1920, 800), (10, 10, 10))
    cx = 1920 // 2
    for y in range(800):
        im.putpixel((cx, y), (0, 255, 0))
    im.save(src)
    dest = tmp_path / "out.png"
    cover_crop(src, dest, 16, 9)
    out = Image.open(dest)
    mid = out.size[0] // 2
    assert out.getpixel((mid, 10)) == (0, 255, 0)
