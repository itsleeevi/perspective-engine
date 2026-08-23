"""Shorts CTA end card and 9:16 thumbnail."""

from __future__ import annotations

from pathlib import Path

from PIL import Image

from channel.compile import fixture_dict
from channel.schema import ShortPlan, VideoMetadata
from channel.shorts import (
    SHORT_CTA,
    attach_short_cta_scene,
    ensure_short_cta,
    is_short_cta,
    render_short_end_card,
    strip_short_cta,
    write_short_thumbnail_job,
)
from channel.thumbnail import render_short_thumbnail_jpeg
from tests.test_channel import _project


def test_ensure_short_cta_replaces_old_line():
    text = (
        "He thought Bill copied the Mac and never had any taste. "
        "The full story is on this channel."
    )
    out = ensure_short_cta(text)
    assert out.endswith(SHORT_CTA)
    assert "full story is on this channel" not in out.lower()
    assert is_short_cta(SHORT_CTA)
    assert strip_short_cta(out) == (
        "He thought Bill copied the Mac and never had any taste."
    )


def test_short_fixture_puts_cta_on_its_own_beat():
    project = _project()
    project.short = ShortPlan(
        short_title="Why the letter still fools people",
        short_narration=(
            "He wrote that God is human weakness. Then he told a rabbi he "
            "believed. The full story is on this channel."
        ),
        long_video_connection="long",
    )
    data = fixture_dict(project, short=True)
    assert data["levels"][-1]["beats"][-1] == SHORT_CTA
    assert data["levels"][-1]["name"] == "The Link"
    blob = " ".join(data["levels"][0]["beats"]).lower()
    assert "full story is on this channel" not in blob


def test_attach_short_cta_scene_appends_once():
    chunks = ["Hook line.", SHORT_CTA]
    scenes = attach_short_cta_scene([], chunks)
    assert len(scenes) == 1
    assert scenes[0].visual_type == "end_card"
    again = attach_short_cta_scene(scenes, chunks)
    assert len(again) == 1


def test_render_short_end_card_is_9_by_16(tmp_path: Path):
    dest = tmp_path / "cta.png"
    render_short_end_card(dest)
    with Image.open(dest) as img:
        assert img.size == (1080, 1920)


def test_render_short_thumbnail_jpeg(tmp_path: Path):
    src = tmp_path / "still.png"
    Image.new("RGB", (1024, 1536), (30, 40, 80)).save(src)
    dest = tmp_path / "thumb.jpg"
    render_short_thumbnail_jpeg(src, dest, "NO TASTE")
    with Image.open(dest) as img:
        assert img.size == (1080, 1920)
    assert dest.stat().st_size > 1000


def test_short_thumbnail_job_is_9_by_16_and_strips_names(tmp_path: Path):
    project = _project()
    project.metadata = VideoMetadata(
        title=project.title,
        description="x" * 40,
        thumbnail_concept="Wild-haired man large in the upper half.",
        thumbnail_text="NOT THAT GOD",
    )
    job = write_short_thumbnail_job(project, root=tmp_path)
    blob = job.read_text(encoding="utf-8")
    assert '"aspect": "9:16"' in blob
    assert "Einstein" not in blob
    assert "Albert" not in blob
    assert "short_thumbnail_1080x1920.jpg" in blob
