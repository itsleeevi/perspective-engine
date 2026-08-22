"""Shared image helpers for the custom-video scripts."""

from __future__ import annotations

from pathlib import Path

from PIL import Image


def cover_crop(
    src: Path,
    dest: Path,
    ratio_w: int,
    ratio_h: int,
    *,
    keep_top: bool = True,
) -> None:
    """Cover-crop to the target aspect so the image FILLS the frame.

    Grok stills are typically 3:2 (1536×1024). A *centered* 16:9 crop takes
    ~80px off the top and shears any on-image label sitting in that band.
    Channel stills put badges top-left, so extra height is taken from the
    bottom. Extra width stays centered (subjects are composed mid-frame).
    """
    im = Image.open(src).convert("RGB")
    w, h = im.size
    target = ratio_w / ratio_h
    if w / h > target:
        nw = int(h * target)
        left = (w - nw) // 2
        im = im.crop((left, 0, left + nw, h))
    else:
        nh = int(w / target)
        top = 0 if keep_top else (h - nh) // 2
        if top + nh > h:
            top = h - nh
        im = im.crop((0, top, w, top + nh))
    dest.parent.mkdir(parents=True, exist_ok=True)
    im.save(dest, "PNG")
