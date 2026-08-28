"""Voice-first HITL: pause detection, ingest, wait states, imported assemble."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest
from PIL import Image

from adapters.voice.imported import ImportedVoiceAdapter
from channel.compile import compile_project
from channel.generate import resume_job, start_job
from channel.ingest import ingest_audio, ingest_images, map_serial_stills, match_images, stage_images
from channel.io import load_project, save_project
from channel.job import JobState, load_manifest
from channel.pauses import (
    Word,
    detect_pauses,
    expected_image_name,
    scenes_from_words,
    timestamp_table,
    write_timestamps,
    write_tone_silence_wav,
)
from channel.schema import Scene, ScenePurpose


def test_scenes_from_word_gaps():
    words = [
        Word("Tonight", 0.0, 0.4),
        Word("you", 0.45, 0.7),
        Word("wait", 1.2, 1.5),
        Word("here", 1.55, 1.9),
    ]
    scenes = scenes_from_words(words, duration=2.0, pause_ms=280)
    assert len(scenes) == 2
    assert scenes[0].start == 0.0
    assert scenes[1].start == pytest.approx(1.2, abs=0.05)
    assert "Tonight" in scenes[0].text
    assert "wait" in scenes[1].text
    assert scenes[0].filename.startswith("000_")
    assert expected_image_name(1, scenes[1].start).endswith(".png")


def test_short_flashes_merge():
    words = [
        Word("A", 0.0, 0.2),
        Word("B", 0.55, 0.7),  # 0.35s gap >= 280ms, but first scene would be 0.55s
        Word("C", 1.4, 1.8),
    ]
    scenes = scenes_from_words(words, duration=2.0, pause_ms=280, min_scene=0.5)
    assert all(s.duration >= 0.5 - 1e-6 for s in scenes)


def test_synthetic_wav_silence_splits(tmp_path: Path):
    wav = write_tone_silence_wav(
        tmp_path / "vo.wav", tone_seconds=1.0, silence_seconds=0.5, repeats=2
    )
    table = detect_pauses(wav, pause_ms=280, words=[])
    assert table["scene_count"] >= 2
    assert table["scenes"][0]["start"] == 0.0
    assert table["scenes"][-1]["end"] == pytest.approx(table["duration_seconds"], abs=0.05)


def test_resume_stops_at_wait_audio(tmp_path: Path):
    first = start_job(
        title="How Nvidia Took Over AI",
        channel="how_they_took_over",
        skip_seed=True,
        artifacts_root=tmp_path,
        job_id="hitl-wait-audio__test__aaa",
    )
    dest = tmp_path / first.job_id
    project = load_project(dest / "project.json")
    from channel.schema import Chapter, StoryPlan

    project.story = StoryPlan(
        hook="The stall looked empty.",
        central_question=project.analysis.core_question,
        initial_assumption="a",
        first_reveal="b",
        major_contradiction="c",
        turning_point="d",
        final_answer="They won the board.",
        title_payoff="They won the board.",
        next_video_bridge="next",
        signature_prop="the board",
        chapters=[
            Chapter(
                name="The Stall",
                purpose=ScenePurpose.hook,
                narration="The stall looked empty. Then the line formed. " * 40,
            )
        ],
    )
    project.scenes = []
    save_project(project, dest / "project.json")
    second = resume_job(first.job_id, artifacts_root=tmp_path, force=True)
    assert second.state is JobState.wait_audio
    assert (dest / "OPERATOR.md").is_file()
    assert "ingest-audio" in (dest / "OPERATOR.md").read_text()
    assert (dest / "script.txt").is_file()
    spec = json.loads(
        (dest / "fixtures" / "video_specs" / "nvidia-took-over-ai.json").read_text()
    )
    assert spec["voice"] == "imported"
    assert not (dest / "flow_prompts.txt").is_file()


def test_ingest_audio_and_images_and_imported_durations(tmp_path: Path):
    job = start_job(
        title="How Nvidia Took Over AI",
        channel="how_they_took_over",
        smoke_test=True,
        skip_seed=True,
        artifacts_root=tmp_path,
        job_id="hitl-ingest__test__bbb",
    )
    dest = tmp_path / job.job_id
    wav = write_tone_silence_wav(tmp_path / "src.wav", tone_seconds=0.8, silence_seconds=0.4, repeats=2)
    table = ingest_audio(job.job_id, wav, artifacts_root=tmp_path, pause_ms=280)
    assert (dest / "timestamps.json").is_file()
    assert (dest / "transcript.txt").is_file()
    assert load_manifest(job.job_id, root=tmp_path).state is JobState.pauses_detected
    names = [row["filename"] for row in table["scenes"]]
    folder = tmp_path / "pngs"
    folder.mkdir()
    for name in names:
        Image.new("RGB", (64, 36), (20, 20, 20)).save(folder / name)
    copied = ingest_images(job.job_id, folder, artifacts_root=tmp_path)
    assert len(copied) == len(names)
    assert load_manifest(job.job_id, root=tmp_path).state is JobState.images_ingested
    matched = match_images(dest / "images", names)
    assert [p.name for p in matched] == names


def test_zapi_serial_maps_one_based_queue(tmp_path: Path):
    expected = ["000_00-00-00.png", "001_00-03-09.png", "002_00-06-21.png"]
    folder = tmp_path / "zapi"
    folder.mkdir()
    Image.new("RGB", (32, 18), (10, 10, 10)).save(folder / "02_red_cabin.jpg")
    Image.new("RGB", (32, 18), (20, 20, 20)).save(folder / "03_red_cabin.jpg")
    Image.new("RGB", (32, 18), (30, 30, 30)).save(folder / "02_red_cabin (1).jpg")
    mapped = map_serial_stills(folder, expected)
    assert mapped[0] is None
    assert mapped[1] is not None and mapped[1].name == "02_red_cabin.jpg"
    assert mapped[2] is not None and mapped[2].name == "03_red_cabin.jpg"


def test_ingest_images_remaps_zapi_serials(tmp_path: Path):
    job = start_job(
        title="How Nvidia Took Over AI",
        channel="how_they_took_over",
        smoke_test=True,
        skip_seed=True,
        artifacts_root=tmp_path,
        job_id="hitl-zapi__test__ddd",
    )
    dest = tmp_path / job.job_id
    wav = write_tone_silence_wav(tmp_path / "src.wav", tone_seconds=0.8, silence_seconds=0.4, repeats=2)
    table = ingest_audio(job.job_id, wav, artifacts_root=tmp_path, pause_ms=280)
    names = [row["filename"] for row in table["scenes"]]
    folder = tmp_path / "zapi"
    folder.mkdir()
    for i, _name in enumerate(names, start=1):
        Image.new("RGB", (64, 36), (i, i, i)).save(folder / f"{i:02d}_red_cabin.jpg")
    copied = ingest_images(job.job_id, folder, artifacts_root=tmp_path)
    assert [p.name for p in copied] == names
    still = Image.open(dest / "images" / names[0])
    assert still.size == (3840, 2160)
    assert load_manifest(job.job_id, root=tmp_path).state is JobState.images_ingested


def test_stage_images_partial_zapi_serials(tmp_path: Path):
    job = start_job(
        title="How Nvidia Took Over AI",
        channel="how_they_took_over",
        smoke_test=True,
        skip_seed=True,
        artifacts_root=tmp_path,
        job_id="hitl-zapi-partial__test__eee",
    )
    dest = tmp_path / job.job_id
    wav = write_tone_silence_wav(tmp_path / "src.wav", tone_seconds=0.8, silence_seconds=0.4, repeats=2)
    table = ingest_audio(job.job_id, wav, artifacts_root=tmp_path, pause_ms=280)
    names = [row["filename"] for row in table["scenes"]]
    folder = tmp_path / "zapi"
    folder.mkdir()
    Image.new("RGB", (64, 36), (40, 40, 40)).save(folder / "02_red_cabin.jpg")
    staged = stage_images(job.job_id, folder, artifacts_root=tmp_path)
    assert names[1] in staged["copied"]
    assert names[0] in staged["missing"]
    staged_still = Image.open(dest / "images" / names[1])
    assert staged_still.size == (3840, 2160)
    copied = ingest_images(
        job.job_id, folder, artifacts_root=tmp_path, require_complete=False
    )
    assert len(copied) >= 1
    assert load_manifest(job.job_id, root=tmp_path).state is JobState.pauses_detected

    import asyncio

    adapter = ImportedVoiceAdapter(dest / "audio" / "voiceover.wav", dest / "timestamps.json")
    result = asyncio.run(adapter.synthesize(["a"] * len(names), [1.0] * len(names)))
    assert result.cost_usd == 0.0
    assert len(result.beat_durations) == len(names)
    assert sum(result.beat_durations) == pytest.approx(table["duration_seconds"], abs=0.08)


def test_compile_flow_prompts_one_to_one(tmp_path: Path):
    from tests.test_channel import _project

    project = _project()
    words = [
        Word("He", 0.0, 0.3),
        Word("waited", 0.9, 1.4),
    ]
    scenes = scenes_from_words(words, 1.8, pause_ms=280)
    table = timestamp_table(scenes, 1.8, audio="audio/voiceover.wav")
    write_timestamps(table, tmp_path / "timestamps.json")
    project.scenes = [
        Scene(
            scene_id=f"scene_{i:03d}",
            narration=row["text"],
            purpose=ScenePurpose.hook,
            action="Wide empty study, one oversized lamp.",
            composition="wide shot",
            who="empty",
            start_seconds=row["start"],
            end_seconds=row["end"],
        )
        for i, row in enumerate(table["scenes"])
    ]
    written = compile_project(project, root=tmp_path, timestamps=table)
    prompts = Path(written["flow_prompts"]).read_text(encoding="utf-8")
    parts = [p for p in prompts.split("\n\n") if p.strip()]
    assert len(parts) == len(table["scenes"])
    assert parts[0].startswith("[00:00]")
    batch_lines = [
        p for p in (tmp_path / "flow_batches.txt").read_text(encoding="utf-8").splitlines() if p.strip()
    ]
    assert len(batch_lines) == len(parts)
    assert batch_lines[0].startswith("[00:00]")
    spec = json.loads(Path(written["spec"]).read_text())
    assert spec["voice"] == "imported"
    jobs = json.loads(Path(written["jobs"]).read_text())
    assert jobs["jobs"][0]["filename"] == table["scenes"][0]["filename"]


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg required to assemble")
def test_assemble_uses_pause_durations(tmp_path: Path):
    job = start_job(
        title="How Nvidia Took Over AI",
        channel="how_they_took_over",
        smoke_test=True,
        skip_seed=True,
        artifacts_root=tmp_path,
        job_id="hitl-assemble__test__ccc",
    )
    dest = tmp_path / job.job_id
    wav = write_tone_silence_wav(tmp_path / "vo.wav", tone_seconds=0.6, silence_seconds=0.4, repeats=2)
    table = ingest_audio(job.job_id, wav, artifacts_root=tmp_path, pause_ms=280)
    folder = tmp_path / "pngs"
    folder.mkdir()
    for row in table["scenes"]:
        Image.new("RGB", (128, 72), (30, 40, 50)).save(folder / row["filename"])
    ingest_images(job.job_id, folder, artifacts_root=tmp_path)
    from channel.assemble_hitl import assemble_hitl

    video = assemble_hitl(job.job_id, artifacts_root=tmp_path)
    assert video.is_file()
    assert video.stat().st_size > 1000
    assert load_manifest(job.job_id, root=tmp_path).state is JobState.ready
