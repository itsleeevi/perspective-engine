"""Lyria 3 (lyria-3-clip-preview) background music: HTTP client + job runner."""

from __future__ import annotations

import base64
import json
from pathlib import Path

import httpx
import pytest

from channel.engine import GEMINI_MUSIC_LOCK
from channel.gemini_music import (
    LYRIA_CLIP_MODEL,
    LYRIA_FULL_MODEL,
    GeminiMusicError,
    LyriaMusicResult,
    _mix_filter,
    generate_job_music,
    generate_music,
    matching_music,
    music_prompt_for,
    normalize_lyria_model,
    suffix_for_mime,
)
from channel.job import (
    GenerationManifest,
    JobState,
    ensure_job_tree,
    write_manifest,
)
from channel.modes import ChannelMode


FAKE_MP3 = b"ID3" + b"\x00" * 64


def _audio_payload(data: bytes | None = None, *, mime: str = "audio/mpeg") -> dict:
    blob = data if data is not None else FAKE_MP3
    return {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {"text": '{"bpm": 72, "instrumental": true}'},
                        {
                            "inlineData": {
                                "mimeType": mime,
                                "data": base64.b64encode(blob).decode("ascii"),
                            }
                        },
                    ]
                }
            }
        ],
        "usageMetadata": {"promptTokenCount": 40, "candidatesTokenCount": 12},
    }


def _ready_job(tmp_path: Path, *, ready: bool = True) -> tuple[str, Path]:
    job_id = "lyria-clip__test__aaa"
    dest = ensure_job_tree(job_id, root=tmp_path)
    manifest = GenerationManifest(
        job_id=job_id,
        created_at="2026-09-20T00:00:00+00:00",
        channel_mode="how_they_took_over",
        title="How Nvidia Took Over AI",
        slug="nvidia-took-over-ai",
        state=JobState.images_ingested,
        qa={"ready_to_publish": ready, "originality_score": 88},
    )
    write_manifest(manifest, root=tmp_path)
    return job_id, dest


def test_normalize_and_prompt_are_instrumental():
    assert normalize_lyria_model("") == LYRIA_CLIP_MODEL
    assert normalize_lyria_model("lyra-3") == LYRIA_CLIP_MODEL
    assert normalize_lyria_model("lyria-3.5") == LYRIA_FULL_MODEL
    assert normalize_lyria_model("", full=True) == LYRIA_FULL_MODEL
    prompt = music_prompt_for(ChannelMode.how_they_took_over, "How Nvidia Took Over AI")
    assert "Instrumental only" in prompt
    assert "no vocals" in prompt
    assert "30-second" in prompt
    assert "Nvidia" in prompt
    full = music_prompt_for(ChannelMode.wealth_pov, extra="warm dusk", full=True)
    assert "two minutes" in full
    assert "warm dusk" in full
    assert suffix_for_mime("audio/wav") == ".wav"
    assert suffix_for_mime("audio/mpeg") == ".mp3"


def test_mix_filter_keeps_narration_first():
    text = _mix_filter(0.12, 2.0, 3.0, 60.0)
    assert "volume=0.1200" in text
    assert "amix=inputs=2:duration=first" in text
    assert "afade=t=out:st=57.00" in text


def test_generate_music_reads_inline_mp3():
    captured: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        captured["body"] = body
        captured["url"] = str(request.url)
        assert request.headers["x-goog-api-key"] == "test-key"
        assert body["contents"][0]["parts"][0]["text"]
        return httpx.Response(200, json=_audio_payload())

    client = httpx.Client(transport=httpx.MockTransport(handler))
    result = generate_music(
        "Instrumental only, no vocals.",
        api_key="test-key",
        client=client,
    )
    assert result.data == FAKE_MP3
    assert "lyria-3-clip-preview:generateContent" in captured["url"]
    assert "instrumental" in result.text.lower()


def test_generate_music_missing_key():
    with pytest.raises(GeminiMusicError, match="GEMINI_API_KEY"):
        generate_music("bed", api_key="")


def test_generate_job_music_writes_mp3(tmp_path: Path):
    job_id, dest = _ready_job(tmp_path)
    calls: list[str] = []

    def fake(prompt: str, **kwargs):
        calls.append(prompt)
        return LyriaMusicResult(data=FAKE_MP3, mime="audio/mpeg", text="ok")

    result = generate_job_music(
        job_id,
        artifacts_root=tmp_path,
        generate=fake,
        api_key="unused",
    )
    bed = dest / "audio" / "music.mp3"
    assert bed.is_file()
    assert bed.read_bytes() == FAKE_MP3
    assert result["generated"] == 1
    assert "Instrumental only" in calls[0]
    ledger = json.loads((dest / "audio" / "music_ledger.json").read_text())
    assert ledger["model"] == LYRIA_CLIP_MODEL
    assert ledger["public_name"] == "Lyria 3 Clip"
    assert ledger["instrumental"] is True
    assert matching_music(dest) == bed


def test_generate_job_music_skips_existing(tmp_path: Path):
    job_id, dest = _ready_job(tmp_path)
    existing = dest / "audio" / "music.mp3"
    existing.parent.mkdir(parents=True, exist_ok=True)
    existing.write_bytes(b"old-bed")
    calls: list[str] = []

    def fake(prompt: str, **kwargs):
        calls.append(prompt)
        return LyriaMusicResult(data=FAKE_MP3)

    result = generate_job_music(
        job_id,
        artifacts_root=tmp_path,
        generate=fake,
        api_key="unused",
    )
    assert result["skipped"] == 1
    assert result["generated"] == 0
    assert calls == []
    assert existing.read_bytes() == b"old-bed"


def test_generate_job_music_blocks_without_qa(tmp_path: Path):
    job_id, _dest = _ready_job(tmp_path, ready=False)
    with pytest.raises(GeminiMusicError, match="ready_to_publish"):
        generate_job_music(
            job_id,
            artifacts_root=tmp_path,
            generate=lambda prompt, **kwargs: (_ for _ in ()).throw(AssertionError()),
            api_key="unused",
        )


def test_generate_job_music_dry_run(tmp_path: Path):
    job_id, dest = _ready_job(tmp_path)
    result = generate_job_music(
        job_id,
        artifacts_root=tmp_path,
        dry_run=True,
        api_key="",
    )
    assert result["dry_run"] is True
    assert result["generated"] == 0
    assert (dest / "audio" / "music.prompt.txt").is_file()
    assert not (dest / "audio" / "music.mp3").is_file()
    assert "Instrumental only" in (dest / "audio" / "music.prompt.txt").read_text()


def test_matching_music_from_drop(tmp_path: Path):
    job = tmp_path / "job"
    (job / "drop").mkdir(parents=True)
    bed = job / "drop" / "music.wav"
    bed.write_bytes(b"RIFF")
    assert matching_music(job) == bed


def test_music_cli_help_and_operator_notes(tmp_path: Path):
    job_id, _dest = _ready_job(tmp_path)
    from channel.job import load_manifest, write_operator_md

    manifest = load_manifest(job_id, root=tmp_path)
    text = write_operator_md(manifest, root=tmp_path).read_text(encoding="utf-8")
    assert "python -m channel music" in text
    assert "lyria-3-clip-preview" in text
    from channel.__main__ import main

    with pytest.raises(SystemExit) as excinfo:
        main(["music", "--help"])
    assert excinfo.value.code == 0


def test_engine_lock():
    assert GEMINI_MUSIC_LOCK["model"] == "lyria-3-clip-preview"
    assert GEMINI_MUSIC_LOCK["full_model"] == "lyria-3.5"
    assert GEMINI_MUSIC_LOCK["opt_in"] is True
