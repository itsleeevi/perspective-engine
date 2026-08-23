"""YouTube channel profile + banner at official upload sizes.

Profile (channel icon): 800×800, designed for a circular crop. Official help
says the icon renders at 98×98; 800×800 is the creator upload size so it
stays sharp.

Banner (channel art): 2560×1440, 16:9, ≤6 MB. YouTube crops this per device.
The only rectangle that survives TV, desktop, tablet, and mobile is the
centered 1546×423 safe area (scaled from the official 1235×338 safe area
at the 2048×1152 minimum).
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

from channel.modes import is_business, is_takeover
from channel.youtube import youtube_dir
from scripts._media import cover_crop

# Official YouTube Help: recommended banner, especially for TV.
BANNER_W, BANNER_H = 2560, 1440
BANNER_MIN_W, BANNER_MIN_H = 2048, 1152
BANNER_MAX_BYTES = 6 * 1024 * 1024
# Official safe area at minimum upload, scaled to the recommended canvas.
SAFE_W = round(1235 * BANNER_W / BANNER_MIN_W)  # 1544
SAFE_H = round(338 * BANNER_H / BANNER_MIN_H)  # 423
# Creator-standard icon upload. Displayed circular at ~98×98.
PROFILE_W, PROFILE_H = 800, 800
PROFILE_MAX_BYTES = 15 * 1024 * 1024


def _save_jpeg(im: Image.Image, dest: Path, max_bytes: int) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    quality = 92
    while quality >= 70:
        im.save(dest, "JPEG", quality=quality, optimize=True)
        if dest.stat().st_size <= max_bytes:
            return dest
        quality -= 4
    return dest


def render_profile_jpeg(
    src: Path, dest: Path | None = None, *, mode: str | None = None
) -> Path:
    """Cover-crop to a centered 800×800 square for the circular icon."""
    dest = dest or branding_paths(mode=mode)["profile"]
    tmp = dest.with_suffix(".work.png")
    cover_crop(src, tmp, 1, 1, keep_top=False)
    im = Image.open(tmp).convert("RGB")
    im = im.resize((PROFILE_W, PROFILE_H), Image.Resampling.LANCZOS)
    tmp.unlink(missing_ok=True)
    return _save_jpeg(im, dest, PROFILE_MAX_BYTES)


def render_banner_jpeg(
    src: Path, dest: Path | None = None, *, mode: str | None = None
) -> Path:
    """Cover-crop to 16:9 (centered) and scale to 2560×1440."""
    dest = dest or branding_paths(mode=mode)["banner"]
    tmp = dest.with_suffix(".work.png")
    cover_crop(src, tmp, 16, 9, keep_top=False)
    im = Image.open(tmp).convert("RGB")
    im = im.resize((BANNER_W, BANNER_H), Image.Resampling.LANCZOS)
    tmp.unlink(missing_ok=True)
    return _save_jpeg(im, dest, BANNER_MAX_BYTES)


def write_banner_safezone_preview(
    banner: Path, dest: Path | None = None, *, mode: str | None = None
) -> Path:
    """Preview only — do not upload. Shows the all-device safe rectangle."""
    dest = dest or branding_paths(mode=mode)["preview"]
    im = Image.open(banner).convert("RGB")
    if im.size != (BANNER_W, BANNER_H):
        im = im.resize((BANNER_W, BANNER_H), Image.Resampling.LANCZOS)
    overlay = Image.new("RGBA", im.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    x0 = (BANNER_W - SAFE_W) // 2
    y0 = (BANNER_H - SAFE_H) // 2
    # Dim everything outside the safe band.
    dim = (0, 0, 0, 110)
    draw.rectangle((0, 0, BANNER_W, y0), fill=dim)
    draw.rectangle((0, y0 + SAFE_H, BANNER_W, BANNER_H), fill=dim)
    draw.rectangle((0, y0, x0, y0 + SAFE_H), fill=dim)
    draw.rectangle((x0 + SAFE_W, y0, BANNER_W, y0 + SAFE_H), fill=dim)
    draw.rectangle(
        (x0, y0, x0 + SAFE_W - 1, y0 + SAFE_H - 1),
        outline=(245, 197, 66, 220),
        width=6,
    )
    out = Image.alpha_composite(im.convert("RGBA"), overlay).convert("RGB")
    dest.parent.mkdir(parents=True, exist_ok=True)
    out.save(dest, "JPEG", quality=88, optimize=True)
    return dest


def branding_paths(root: Path | None = None, *, mode: str | None = None) -> dict[str, Path]:
    dest = youtube_dir(root)
    if is_takeover(mode):
        return {
            "profile": dest / "how_they_took_over_profile_800x800.jpg",
            "banner": dest / "how_they_took_over_cover_2560x1440.jpg",
            "preview": dest / "how_they_took_over_cover_safezone_preview.jpg",
            "about": dest / "how_they_took_over_about.txt",
            "handle": dest / "how_they_took_over_handle.txt",
        }
    if is_business(mode):
        return {
            "profile": dest / "behind_the_business_profile_800x800.jpg",
            "banner": dest / "behind_the_business_cover_2560x1440.jpg",
            "preview": dest / "behind_the_business_cover_safezone_preview.jpg",
            "about": dest / "behind_the_business_about.txt",
            "handle": dest / "behind_the_business_handle.txt",
        }
    return {
        "profile": dest / "channel_profile_800x800.jpg",
        "banner": dest / "channel_cover_2560x1440.jpg",
        "preview": dest / "channel_cover_safezone_preview.jpg",
        "about": dest / "channel_about.txt",
        "handle": dest / "channel_handle.txt",
    }


def write_channel_copy(*, mode: str | None = None, root: Path | None = None) -> dict[str, Path]:
    """Write About + handle text next to the sized JPEGs."""
    from channel.config import config_for

    cfg = config_for(mode)
    paths = branding_paths(root, mode=mode)
    paths["about"].parent.mkdir(parents=True, exist_ok=True)
    paths["about"].write_text(cfg.channel_about, encoding="utf-8")
    handle = getattr(cfg, "channel_handle", "") or ""
    if handle:
        paths["handle"].write_text(handle.strip() + "\n", encoding="utf-8")
    return paths
