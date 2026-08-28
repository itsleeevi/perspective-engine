"""Drop-folder cuts: filename clocks, 4K upscale, assemble without burned captions."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from unittest.mock import patch

import pytest
from PIL import Image

from channel.drop import (
    ingest_drop,
    list_timestamped_stills,
    parse_still_start,
    start_drop_job,
    timestamps_from_stills,
)
from channel.job import JobState, load_manifest
from channel.pauses import write_tone_silence_wav


def test_parse_bracket_mmss_from_flow_export():
    assert parse_still_start("[00-00]_Hand-drawn_2D_doo.jpg") == 0.0
    assert parse_still_start("[00-13]_Hand-drawn_2D_doo.jpg") == 13.0
    assert parse_still_start("[01-01]_Hand-drawn_2D_doo.jpg") == 61.0
    assert parse_still_start("[00:05]_still.png") == 5.0
    assert parse_still_start("[01-12-05]_wide.jpg") == 1 * 3600 + 12 * 60 + 5
    assert parse_still_start("000_00-00-04.png") == pytest.approx(4 / 30)
    assert parse_still_start("readme.md") is None
    assert parse_still_start("02_red_cabin.jpg") is None


def test_duplicate_clock_prefers_clean_filename(tmp_path: Path):
    Image.new("RGB", (32, 18), (1, 1, 1)).save(tmp_path / "[00-03]_Hand-drawn_2D_doo.jpg")
    Image.new("RGB", (32, 18), (2, 2, 2)).save(tmp_path / "[00-03]_Hand-drawn_2D_doo (1).jpg")
    rows = list_timestamped_stills(tmp_path)
    assert len(rows) == 1
    assert rows[0][0] == 3.0
    assert rows[0][1].name == "[00-03]_Hand-drawn_2D_doo.jpg"


def test_timestamps_hold_until_next_and_audio_end(tmp_path: Path):
    a = tmp_path / "[00-00]_a.jpg"
    b = tmp_path / "[00-03]_b.jpg"
    a.write_bytes(b"x")
    b.write_bytes(b"x")
    scenes, sources = timestamps_from_stills([(0.0, a), (3.0, b)], duration=10.0)
    assert [s.start for s in scenes] == [0.0, 3.0]
    assert scenes[0].end == 3.0
    assert scenes[1].end == 10.0
    assert sources[0] == a
    assert sources[1] == b


def test_first_still_covers_from_zero(tmp_path: Path):
    a = tmp_path / "[00-03]_a.jpg"
    b = tmp_path / "[00-05]_b.jpg"
    scenes, sources = timestamps_from_stills([(3.0, a), (5.0, b)], duration=8.0)
    assert scenes[0].start == 0.0
    assert scenes[0].end == 5.0
    assert sources[0] == a
    assert scenes[1].start == 5.0
    assert scenes[1].end == 8.0


def test_drop_job_writes_folder_and_wait_state(tmp_path: Path):
    manifest = start_drop_job(
        title="How Nvidia Took Over AI",
        channel="how_they_took_over",
        artifacts_root=tmp_path,
        job_id="drop-wait__test__aaa",
    )
    dest = tmp_path / manifest.job_id
    drop = dest / "drop"
    assert drop.is_dir()
    readme = (drop / "README.md").read_text(encoding="utf-8")
    assert "[00-00]" in readme
    assert "without burned captions" in readme
    assert manifest.state is JobState.wait_drop
    operator = (dest / "OPERATOR.md").read_text(encoding="utf-8")
    assert "[00-00]" in operator
    assert "without burned captions" in operator


def test_ingest_drop_upscales_to_4k_and_cuts_on_filename_clocks(tmp_path: Path):
    job = start_drop_job(
        title="How Nvidia Took Over AI",
        channel="how_they_took_over",
        artifacts_root=tmp_path,
        job_id="drop-ingest__test__bbb",
    )
    dest = tmp_path / job.job_id
    drop = dest / "drop"
    Image.new("RGB", (64, 36), (20, 20, 20)).save(drop / "[00-00]_Hand-drawn_2D_doo.jpg")
    Image.new("RGB", (64, 36), (40, 40, 40)).save(drop / "[00-01]_Hand-drawn_2D_doo.jpg")
    wav = write_tone_silence_wav(
        drop / "voiceover.wav", tone_seconds=0.8, silence_seconds=0.4, repeats=2
    )
    assert wav.is_file()
    table = ingest_drop(job.job_id, artifacts_root=tmp_path)
    assert table["cut_source"] == "drop_filename_timestamps"
    assert table["scenes"][0]["start"] == 0.0
    assert table["scenes"][1]["start"] == 1.0
    assert table["scenes"][-1]["end"] == pytest.approx(table["duration_seconds"], abs=0.05)
    still = Image.open(dest / "images" / table["scenes"][0]["filename"])
    assert still.size == (3840, 2160)
    spec = json.loads(
        (dest / "fixtures" / "video_specs" / "nvidia-took-over-ai.json").read_text()
    )
    assert spec["burn_captions"] is False
    assert load_manifest(job.job_id, root=tmp_path).state is JobState.images_ingested


def test_cli_drop_prints_folder(tmp_path: Path, capsys: pytest.CaptureFixture[str]):
    from channel.__main__ import main

    code = main(
        [
            "drop",
            "--channel",
            "how_they_took_over",
            "--title",
            "How Nvidia Took Over AI",
            "--artifacts",
            str(tmp_path),
            "--job-id",
            "drop-cli__test__ccc",
        ]
    )
    assert code == 0
    out = capsys.readouterr().out
    assert "drop:" in out
    assert "[00-00]" in out
    folder = tmp_path / "drop-cli__test__ccc" / "drop"
    assert folder.is_dir()


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg required to assemble")
def test_assemble_drop_does_not_burn_captions(tmp_path: Path):
    job = start_drop_job(
        title="How Nvidia Took Over AI",
        channel="how_they_took_over",
        artifacts_root=tmp_path,
        job_id="drop-assemble__test__ddd",
    )
    dest = tmp_path / job.job_id
    drop = dest / "drop"
    Image.new("RGB", (64, 36), (30, 40, 50)).save(drop / "[00-00]_Hand-drawn_2D_doo.jpg")
    Image.new("RGB", (64, 36), (60, 70, 80)).save(drop / "[00-01]_Hand-drawn_2D_doo.jpg")
    write_tone_silence_wav(
        drop / "voiceover.wav", tone_seconds=0.8, silence_seconds=0.4, repeats=2
    )
    from channel.drop import assemble_drop

    with patch("graph.captions.overlay_scene_caption") as overlay:
        video = assemble_drop(job.job_id, artifacts_root=tmp_path)
    overlay.assert_not_called()
    assert video.is_file()
    assert video.stat().st_size > 1000
    assert load_manifest(job.job_id, root=tmp_path).state is JobState.ready
    spec = json.loads(
        (dest / "fixtures" / "video_specs" / "nvidia-took-over-ai.json").read_text()
    )
    assert spec["burn_captions"] is False
