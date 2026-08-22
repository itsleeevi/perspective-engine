"""Shared image helpers for the custom-video scripts."""

from __future__ import annotations

from pathlib import Path

from PIL import Image


def cover_crop(src: Path, dest: Path, ratio_w: int, ratio_h: int) -> None:
    """Center-crop to the target aspect so the image FILLS the frame."""
    im = Image.open(src).convert("RGB")
    w, h = im.size
    target = ratio_w / ratio_h
    if w / h > target:
        nw = int(h * target)
        left = (w - nw) // 2
        im = im.crop((left, 0, left + nw, h))
    else:
        nh = int(w / target)
        top = (h - nh) // 2
        im = im.crop((0, top, w, top + nh))
    dest.parent.mkdir(parents=True, exist_ok=True)
    im.save(dest, "PNG")
