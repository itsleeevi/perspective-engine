"""Gemini 3.1 Flash TTS: chunk the script, call the API, save wavs."""

from __future__ import annotations

import base64
import json
from pathlib import Path

import httpx
import pytest

from channel.gemini_tts import (
    GEMINI_TTS_MODEL,
    GeminiTtsError,
    auto_tts_enabled,
    chunk_script,
    chunks_for_script,
    concat_wavs,
    spoken_word_count,
    synthesize_job,
    synthesize_pcm,
    transcripts_match_script,
    write_pcm_wav,
)
from channel.generate import resume_job, start_job
from channel.io import load_project, save_project
from channel.modes import ChannelMode
from channel.schema import Chapter, ScenePurpose, StoryPlan


def _sentence(n: int, tag: str) -> str:
    words = " ".join(f"{tag}{i:03d}" for i in range(n))
    return f"{words}."


def _script(*parts: str) -> str:
    return " ".join(parts)


def silence_pcm(seconds: float = 0.05, rate: int = 24000) -> bytes:
    return b"\x00\x00" * int(seconds * rate)


def test_chunk_script_aims_for_working_caps():
    sentences = [_sentence(30, "w") for _ in range(12)]
    script = " ".join(sentences)
    chunks = chunk_script(script)
    assert len(chunks) >= 2
    for text in chunks:
        assert spoken_word_count(text) <= 180
        assert len(text) <= 1200
    packed = chunks_for_script(script, mode=ChannelMode.how_they_took_over)
    assert transcripts_match_script(packed, script)
    assert "#### TRANSCRIPT" in packed[0].prompt
    assert "[whisper]" not in packed[0].prompt


def test_chunk_script_splits_before_char_cap():
    sentence = " ".join(["extraordinarily"] * 70) + "."
    chunks = chunk_script(sentence + " " + sentence)
    assert all(len(c) <= 1200 for c in chunks)
    assert len(chunks) >= 2


def test_synthesize_pcm_reads_inline_audio(monkeypatch):
    pcm = silence_pcm()
    payload = {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {
                            "inlineData": {
                                "mimeType": "audio/L16;codec=pcm;rate=24000",
                                "data": base64.b64encode(pcm).decode("ascii"),
                            }
                        }
                    ]
                }
            }
        ]
    }

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        assert body["generationConfig"]["speechConfig"]["voiceConfig"][
            "prebuiltVoiceConfig"
        ]["voiceName"] == "Charon"
        assert "gemini-3.1-flash-tts-preview" in str(request.url)
        return httpx.Response(200, json=payload)

    transport = httpx.MockTransport(handler)
    client = httpx.Client(transport=transport)
    out = synthesize_pcm("Say hello.", api_key="test-key", client=client)
    assert out == pcm


def test_synthesize_job_saves_chunks(tmp_path: Path):
    first = start_job(
        title="How Nvidia Took Over AI",
        channel="how_they_took_over",
        skip_seed=True,
        artifacts_root=tmp_path,
        job_id="tts-save__test__aaa",
    )
    dest = tmp_path / first.job_id
    project = load_project(dest / "project.json")
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
                narration=_script(*[_sentence(40, "n") for _ in range(8)]),
            )
        ],
    )
    project.scenes = []
    save_project(project, dest / "project.json")
    resume_job(first.job_id, artifacts_root=tmp_path, force=True)
    assert (dest / "script.txt").is_file()
    assert (dest / "tts_chunks.txt").is_file()

    result = synthesize_job(
        first.job_id,
        artifacts_root=tmp_path,
        synthesize=lambda prompt: silence_pcm(0.08),
        api_key="test-key",
    )
    chunk_dir = dest / "audio" / "chunks"
    assert result["chunk_count"] >= 2
    assert (chunk_dir / "000.wav").is_file()
    assert (chunk_dir / "000.txt").is_file()
    assert (chunk_dir / "000.prompt.txt").is_file()
    assert (chunk_dir / "concat_24k.wav").is_file()
    ledger = json.loads((chunk_dir / "ledger.json").read_text())
    assert ledger["model"] == GEMINI_TTS_MODEL
    assert ledger["voice"] == "Charon"
    joined = " ".join(
        (chunk_dir / f"{i:03d}.txt").read_text().strip()
        for i in range(result["chunk_count"])
    )
    script = (dest / "script.txt").read_text()
    from channel.gemini_tts import normalize_ws

    assert normalize_ws(joined) == normalize_ws(script)


def test_chunks_only_does_not_need_a_key(tmp_path: Path):
    job = start_job(
        title="How Nvidia Took Over AI",
        channel="how_they_took_over",
        skip_seed=True,
        artifacts_root=tmp_path,
        job_id="tts-chunks-only__test__bbb",
    )
    dest = tmp_path / job.job_id
    (dest / "script.txt").write_text(_sentence(50, "a") + " " + _sentence(50, "b") + "\n")
    result = synthesize_job(job.job_id, artifacts_root=tmp_path, chunks_only=True)
    assert result["chunks_only"] is True
    assert (dest / "tts_chunks.txt").is_file()
    assert not (dest / "audio" / "chunks" / "000.wav").is_file()


def test_missing_key_fails_clearly_without_fallback(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "")
    monkeypatch.setenv("GOOGLE_API_KEY", "")
    monkeypatch.setenv("GOOGLE_GENAI_API_KEY", "")
    job = start_job(
        title="How Nvidia Took Over AI",
        channel="how_they_took_over",
        skip_seed=True,
        artifacts_root=tmp_path,
        job_id="tts-nokey__test__ccc",
    )
    dest = tmp_path / job.job_id
    (dest / "script.txt").write_text("The stall looked empty. Then the line formed.\n")
    with pytest.raises(GeminiTtsError, match="GEMINI_API_KEY"):
        synthesize_job(job.job_id, artifacts_root=tmp_path)
    assert (dest / "tts_chunks.txt").is_file()


def test_auto_tts_skips_under_pytest():
    assert auto_tts_enabled(auto_tts=None, smoke_test=False, stubs=False) is False


def test_concat_wavs(tmp_path: Path):
    a = write_pcm_wav(tmp_path / "a.wav", silence_pcm(0.04))
    b = write_pcm_wav(tmp_path / "b.wav", silence_pcm(0.04))
    out = concat_wavs([a, b], tmp_path / "out.wav")
    assert out.is_file()
    assert out.stat().st_size > a.stat().st_size


def test_cli_tts_chunks_only(tmp_path: Path):
    from channel.__main__ import main

    job = start_job(
        title="How Nvidia Took Over AI",
        channel="how_they_took_over",
        skip_seed=True,
        artifacts_root=tmp_path,
        job_id="tts-cli__test__ddd",
    )
    dest = tmp_path / job.job_id
    (dest / "script.txt").write_text(_sentence(40, "c") + " " + _sentence(40, "d") + "\n")
    assert (
        main(
            [
                "tts",
                job.job_id,
                "--chunks-only",
                "--artifacts",
                str(tmp_path),
            ]
        )
        == 0
    )
    assert (dest / "tts_chunks.txt").is_file()
    assert "gemini-3.1-flash-tts-preview" in (dest / "tts_chunks.txt").read_text()
