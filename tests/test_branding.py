"""YouTube channel profile and banner must match official upload sizes."""

from __future__ import annotations

from pathlib import Path

from PIL import Image

from channel.branding import (
    BANNER_H,
    BANNER_MAX_BYTES,
    BANNER_W,
    PROFILE_H,
    PROFILE_W,
    SAFE_H,
    SAFE_W,
    render_banner_jpeg,
    render_profile_jpeg,
    write_banner_safezone_preview,
)


def test_safe_area_scales_from_official_minimum():
    # Official: 1235×338 at 2048×1152 → same ratio on 2560×1440.
    assert SAFE_W == round(1235 * 2560 / 2048)
    assert SAFE_H == round(338 * 1440 / 1152)
    assert SAFE_W < BANNER_W
    assert SAFE_H < BANNER_H


def test_btb_branding_paths_do_not_clobber_wtrt():
    from channel.branding import branding_paths

    wtrt = branding_paths()
    btb = branding_paths(mode="behind_the_business")
    htto = branding_paths(mode="how_they_took_over")
    assert wtrt["profile"].name == "channel_profile_800x800.jpg"
    assert btb["profile"].name == "behind_the_business_profile_800x800.jpg"
    assert btb["banner"].name == "behind_the_business_cover_2560x1440.jpg"
    assert btb["about"].name == "behind_the_business_about.txt"
    assert btb["handle"].name == "behind_the_business_handle.txt"
    assert htto["profile"].name == "how_they_took_over_profile_800x800.jpg"
    assert htto["about"].name == "how_they_took_over_about.txt"
    assert htto["handle"].name == "how_they_took_over_handle.txt"
    assert len({wtrt["profile"], btb["profile"], htto["profile"]}) == 3


def test_profile_is_800_square(tmp_path: Path):
    src = tmp_path / "p.png"
    Image.new("RGB", (1200, 900), (20, 30, 60)).save(src)
    dest = tmp_path / "profile.jpg"
    render_profile_jpeg(src, dest)
    out = Image.open(dest)
    assert out.size == (PROFILE_W, PROFILE_H)
    assert dest.stat().st_size < 15 * 1024 * 1024


def test_banner_is_2560x1440_and_under_6mb(tmp_path: Path):
    src = tmp_path / "c.png"
    Image.new("RGB", (1536, 1024), (15, 20, 40)).save(src)
    dest = tmp_path / "banner.jpg"
    render_banner_jpeg(src, dest)
    out = Image.open(dest)
    assert out.size == (BANNER_W, BANNER_H)
    assert dest.stat().st_size <= BANNER_MAX_BYTES
    preview = write_banner_safezone_preview(dest, tmp_path / "preview.jpg")
    assert Image.open(preview).size == (BANNER_W, BANNER_H)
