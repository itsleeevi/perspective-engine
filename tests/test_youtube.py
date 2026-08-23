"""YouTube pack: description, tags, 1280×720 thumbnail overlay."""

from __future__ import annotations

from pathlib import Path

from PIL import Image

from channel.config import SYNTHETIC_DISCLOSURE
from channel.thumbnail import render_thumbnail_jpeg
from channel.youtube import (
    chapter_lines,
    long_description,
    tags_line,
    thumbnail_prompt,
    write_pack,
    write_thumbnail_job,
)


def test_long_description_leads_with_search_phrase_and_disclosure():
    text = long_description(
        {
            "title": "What Einstein Really Thought About Religion",
            "description": (
                "What Einstein really thought about religion: he thought God was "
                "the order of the universe, not a person who listens.\n\n"
                "A rabbi paid for a telegram."
            ),
        },
        ["0:00 Intro", "0:13 The Telegram"],
    )
    assert text[:200].startswith("What Einstein really thought about religion")
    assert "0:00 Intro" in text
    assert "0:13 The Telegram" in text
    assert SYNTHETIC_DISCLOSURE in text
    assert text.count("Synthetic media:") == 1


def test_chapter_lines_force_zero_intro():
    lines = chapter_lines(
        [
            {"start_seconds": 13.29, "label": "The Telegram"},
            {"start_seconds": 46.38, "label": "The Door"},
        ]
    )
    assert lines[0] == "0:00 Intro"
    assert lines[1] == "0:13 The Telegram"
    assert lines[2] == "0:46 The Door"


def test_tags_line_stays_under_budget():
    line = tags_line(["einstein"] * 80)
    assert len(line) <= 501
    assert line.startswith("einstein")


def test_write_pack_and_thumbnail_jpeg(tmp_path: Path):
    spec = {
        "topic": "What Einstein Really Thought About Religion",
        "fixture": "fixtures/einstein-religion.json",
        "youtube": {
            "title": "What Einstein Really Thought About Religion",
            "description": (
                "What Einstein really thought about religion: he thought God was "
                "the order of the universe, not a person who listens.\n\n"
                "Churches quoted him. Atheists quoted him."
            ),
            "thumbnail_text": "NOT THAT\nGOD",
            "short_title": "Why Einstein's God Letter Still Fools People",
            "tags": ["einstein", "religion", "what they really think"],
        },
    }
    assemble = {"chapters": [{"start_seconds": 13.29, "label": "The Telegram"}]}
    pack = write_pack(spec, assemble=assemble, root=tmp_path)
    desc = Path(pack["description"]).read_text(encoding="utf-8")
    assert "What Einstein really thought about religion" in desc[:200]
    assert "0:00 Intro" in desc
    assert "0:13 The Telegram" in desc
    assert SYNTHETIC_DISCLOSURE in desc
    tags = Path(pack["tags"]).read_text(encoding="utf-8")
    assert "einstein" in tags
    short = Path(pack["short_description"]).read_text(encoding="utf-8")
    assert "Why Einstein's God Letter Still Fools People" in short
    assert "Watch the full video. The link is in the description." in short

    src = tmp_path / "still.png"
    Image.new("RGB", (1536, 1024), (30, 40, 80)).save(src)
    dest = tmp_path / "thumb.jpg"
    render_thumbnail_jpeg(src, dest, "NOT THAT\nGOD")
    out = Image.open(dest)
    assert out.size == (1280, 720)
    assert dest.stat().st_size > 1000


def test_thumbnail_prompt_strips_historical_names(tmp_path: Path):
    from channel.schema import VideoMetadata
    from tests.test_channel import _project

    project = _project()
    project.metadata = VideoMetadata(
        title=project.title,
        description="x" * 40,
        thumbnail_concept="Wild-haired man at a desk with a letter.",
        thumbnail_text="NOT THAT GOD",
    )
    prompt = thumbnail_prompt(project)
    job = write_thumbnail_job(project, root=tmp_path)
    blob = prompt + "\n" + job.read_text(encoding="utf-8")
    assert "Einstein" not in blob
    assert "Albert" not in blob
    assert "30 percent" in prompt
    assert "TIGHT crop" in prompt
    assert job.is_file()
