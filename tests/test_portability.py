"""Fresh-clone / Cloud portability. No chat history required."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from channel.config import (
    BEHIND_THE_BUSINESS,
    CHANNEL,
    HOW_THEY_TOOK_OVER,
    config_for,
)
from channel.engine import (
    IMAGE_FILENAME_RULE,
    MODEL_LOCK,
    NO_PROVIDER_FALLBACK,
    VIDEO_ENGINE_VERSION,
    generate_image_filename,
    image_token_for,
)
from channel.generate import resume_job, start_job
from channel.job import ARTIFACTS, load_manifest, resolve_project_path
from channel.paths import ROOT as REPO_ROOT
from channel.paths import relpath_for_spec
from channel.readiness import check_readiness
from channel.title import analyze_title

ROOT = Path(__file__).resolve().parent.parent
GOLDEN = ROOT / "tests" / "fixtures" / "golden"


def test_cloud_readiness_required_files():
    report = check_readiness(strict=False)
    assert report["ok"], report["errors"]
    assert report["engine_version"] == VIDEO_ENGINE_VERSION


def test_model_lock_forbids_silent_fallback():
    assert MODEL_LOCK["tts"] == "kokoro"
    assert "GenerateImage" in MODEL_LOCK["image"]
    assert NO_PROVIDER_FALLBACK is True
    assert "filename" in IMAGE_FILENAME_RULE.lower()


def test_golden_wtrt_jobs_style():
    meta = json.loads((GOLDEN / "wtrt-steve-jobs-bill-gates.json").read_text())
    spec = json.loads((ROOT / meta["spec"]).read_text())
    assert spec["channel"] == "What They Really Think"
    assert spec["voice"] == "kokoro"
    assert CHANNEL.narration_word_min == meta["new_title_word_min"]
    assert meta["visual_style_must_contain"] in CHANNEL.visual_style
    assert meta["visual_style_must_not_contain"] not in CHANNEL.visual_style


def test_golden_btb_costco_lock():
    meta = json.loads((GOLDEN / "btb-costco-really-makes-money.json").read_text())
    spec = json.loads((ROOT / meta["spec"]).read_text())
    assert spec["channel_mode"] == "behind_the_business"
    assert spec["kokoro_speed"] == meta["kokoro_speed"]
    assert BEHIND_THE_BUSINESS.narration_word_min == meta["new_title_word_min"]
    assert "Behind The Business" in BEHIND_THE_BUSINESS.visual_style
    assert "muted historical" not in BEHIND_THE_BUSINESS.visual_style.lower()


def test_golden_htto_nvidia_does_not_assume_cuda():
    meta = json.loads((GOLDEN / "htto-nvidia-took-over-ai.json").read_text())
    analysis = analyze_title(meta["title"], channel_mode=meta["channel_mode"])
    blob = json.dumps(analysis.model_dump()).lower()
    for banned in meta["must_not_assume"]:
        assert banned.lower() not in blob
    assert HOW_THEY_TOOK_OVER.narration_word_min == meta["new_title_word_min"]
    assert HOW_THEY_TOOK_OVER.kokoro_speed == meta["kokoro_speed"]
    assert "How They Took Over" in HOW_THEY_TOOK_OVER.visual_style


def test_generate_smoke_and_parallel_jobs(tmp_path: Path):
    a = start_job(
        title="What Einstein Really Thought About God",
        channel="what_they_really_think",
        smoke_test=True,
        artifacts_root=tmp_path,
        job_id="einstein-god__test__aaa",
    )
    b = start_job(
        title="How Visa Really Makes Money",
        channel="behind_the_business",
        smoke_test=True,
        artifacts_root=tmp_path,
        job_id="visa-money__test__bbb",
    )
    c = start_job(
        title="How Nvidia Took Over AI",
        channel="how_they_took_over",
        smoke_test=True,
        artifacts_root=tmp_path,
        job_id="nvidia-ai__test__ccc",
    )
    assert a.job_id != b.job_id != c.job_id
    assert a.paths["job"] != b.paths["job"]
    assert (tmp_path / a.job_id / "manifest.json").is_file()
    assert (tmp_path / a.job_id / "project.json").is_file()
    assert (tmp_path / a.job_id / "report.txt").is_file()
    assert (tmp_path / c.job_id / "fixtures" / "video_specs").is_dir()
    spec_c = (tmp_path / c.job_id / "fixtures" / "video_specs" / "nvidia-took-over-ai.json")
    assert spec_c.is_file()
    assert "how_they_took_over" in spec_c.read_text()
    assert "visa" not in Path(a.paths["project"]).read_text().lower()
    assert (tmp_path / a.job_id / "characters.json").is_file()
    assert (tmp_path / b.job_id / "company.json").is_file()
    assert (tmp_path / c.job_id / "story.json").is_file()
    jobs_c = tmp_path / c.job_id / "fixtures" / "nvidia-took-over-ai_v1_image_jobs.json"
    assert jobs_c.is_file()
    blob = jobs_c.read_text().lower()
    assert "generate_filename" in blob
    assert "nvidia" not in json.loads(jobs_c.read_text())["jobs"][0]["generate_filename"]
    spec = json.loads(spec_c.read_text())
    assert spec["engine_version"] == VIDEO_ENGINE_VERSION
    assert spec["stills_dir"] == "images"


def test_generate_does_not_mutate_engine_config(tmp_path: Path):
    before = hashlib.sha256((ROOT / "channel" / "config.py").read_bytes()).hexdigest()
    start_job(
        title="What Einstein Really Thought About God",
        channel="What They Really Think",
        smoke_test=True,
        skip_seed=True,
        artifacts_root=tmp_path,
        job_id="no-mutate__test__ddd",
    )
    after = hashlib.sha256((ROOT / "channel" / "config.py").read_bytes()).hexdigest()
    assert before == after


def test_resume_smoke_job(tmp_path: Path):
    first = start_job(
        title="How Nvidia Took Over AI",
        channel="how_they_took_over",
        smoke_test=True,
        artifacts_root=tmp_path,
        job_id="resume-htto__test__eee",
    )
    second = resume_job(first.job_id, artifacts_root=tmp_path, force=True, stubs=True)
    assert second.job_id == first.job_id
    loaded = load_manifest(first.job_id, root=tmp_path)
    assert loaded.engine_version == VIDEO_ENGINE_VERSION
    assert loaded.paths.get("spec")


def test_cli_generate_and_readiness(tmp_path: Path):
    from channel.__main__ import main

    assert main(["cloud-readiness"]) == 0
    assert (
        main(
            [
                "generate",
                "--channel",
                "how_they_took_over",
                "--title",
                "How Nvidia Took Over AI",
                "--smoke-test",
                "--skip-seed",
                "--job-id",
                "cli-htto__test__fff",
                "--artifacts",
                str(tmp_path),
            ]
        )
        == 0
    )
    assert (tmp_path / "cli-htto__test__fff" / "manifest.json").is_file()


def test_fresh_agent_can_route_from_repo_only():
    """Simulate empty chat: AGENTS.md + config are enough to pick commands."""
    agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    assert "python -m channel generate" in agents
    assert "behind_the_business" in agents
    assert "how_they_took_over" in agents
    assert config_for("how_they_really_make_money") is BEHIND_THE_BUSINESS
    start = (ROOT / "docs" / "video-engine" / "CLOUD_AGENT_START_PROMPT.md").read_text()
    assert "--channel" in start
    assert "unique job ID" in start.lower() or "job ID" in start


def test_artifacts_default_is_repo_artifacts():
    assert ARTIFACTS == ROOT / "artifacts"


def test_relpath_keeps_artifacts_jobs_repo_relative():
    dest = REPO_ROOT / "artifacts" / "demo-job" / "fixtures" / "x.json"
    assert relpath_for_spec(dest, root=dest.parent.parent) == (
        "artifacts/demo-job/fixtures/x.json"
    )


def test_generate_filename_has_no_english_words():
    token = image_token_for("nvidia-took-over-ai", "nvidia-took-over-ai__20260823_190000__abc123")
    name = generate_image_filename(0, token=token, kind="scene")
    assert name.startswith("s")
    assert "nvidia" not in name
    assert "costco" not in name


def test_resolve_job_id_from_artifacts(tmp_path: Path):
    start_job(
        title="How Nvidia Took Over AI",
        channel="how_they_took_over",
        smoke_test=True,
        artifacts_root=tmp_path,
        job_id="resolve-htto__test__hhh",
    )
    found = resolve_project_path("resolve-htto__test__hhh", artifacts_root=tmp_path)
    assert found.parent.name == "resolve-htto__test__hhh"


def test_job_file_smoke(tmp_path: Path):
    from channel.__main__ import main

    assert (
        main(
            [
                "generate",
                "--job",
                str(ROOT / "jobs" / "example.json"),
                "--smoke-test",
                "--skip-seed",
                "--job-id",
                "jobfile-htto__test__ggg",
                "--artifacts",
                str(tmp_path),
            ]
        )
        == 0
    )
    assert (tmp_path / "jobfile-htto__test__ggg" / "manifest.json").is_file()
