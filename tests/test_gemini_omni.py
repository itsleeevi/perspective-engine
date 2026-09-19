"""Omni 1.1 Flash (gemini-omni-1.1-flash) image-to-video: HTTP client + job runner."""

from __future__ import annotations

import base64
import io
import json
from pathlib import Path

import httpx
import pytest
from PIL import Image

from adapters.pricing import gemini_omni_video_cost, gemini_omni_video_floor_cost
from adapters.video_gen.gemini_omni import (
    GEMINI_OMNI_VIDEO_MODEL,
    GeminiOmniError,
    GeminiOmniVideoAdapter,
    clamp_omni_duration,
    file_id_from_uri,
    generate_video,
    matching_omni_clip,
    omni_motion_prompt,
    usage_cost,
)
from channel.gemini_videos import GeminiVideosError, generate_job_videos
from channel.job import (
    GenerationManifest,
    JobState,
    ensure_job_tree,
    write_manifest,
)


FAKE_MP4 = b"\x00\x00\x00\x18ftypmp42" + b"\x00" * 32


def tiny_png(color: tuple[int, int, int] = (20, 40, 80)) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (32, 18), color).save(buf, format="PNG")
    return buf.getvalue()


def _inline_payload(mp4: bytes | None = None) -> dict:
    data = mp4 if mp4 is not None else FAKE_MP4
    return {
        "id": "v1_test",
        "status": "completed",
        "model": GEMINI_OMNI_VIDEO_MODEL,
        "steps": [
            {
                "type": "model_output",
                "content": [
                    {
                        "type": "video",
                        "mime_type": "video/mp4",
                        "data": base64.b64encode(data).decode("ascii"),
                    }
                ],
            }
        ],
        "usage": {
            "promptTokensDetails": [
                {"modality": "TEXT", "tokenCount": 40},
                {"modality": "IMAGE", "tokenCount": 1120},
            ],
            "candidatesTokensDetails": [
                {"modality": "VIDEO", "tokenCount": 5792},
            ],
        },
    }


def test_clamp_and_floor_cost():
    assert clamp_omni_duration(1) == 3.0
    assert clamp_omni_duration(12) == 10.0
    assert clamp_omni_duration(5) == 5.0
    assert round(gemini_omni_video_floor_cost("720p", 1), 3) == 0.101
    mixed = gemini_omni_video_cost(40, 1120, 0, 0, 5792)
    assert mixed > gemini_omni_video_floor_cost("720p", 1)


def test_usage_cost_falls_back_to_resolution_tokens():
    cost, summary = usage_cost({}, resolution="720p", duration_seconds=1.0)
    assert summary["video_output_tokens"] == 5792
    assert cost == gemini_omni_video_floor_cost("720p", 1.0)


def test_omni_motion_prompt_keeps_drawn_look():
    text = omni_motion_prompt("two cards on a board", 5, "slow push-in")
    assert "about 5 seconds" in text
    assert "drawn look" in text
    assert "Camera: slow push-in." in text


def test_matching_omni_clip(tmp_path: Path):
    videos = tmp_path / "videos"
    videos.mkdir()
    still = tmp_path / "000_00-00-00.png"
    still.write_bytes(tiny_png())
    assert matching_omni_clip(videos, still) is None
    clip = videos / "000_00-00-00.mp4"
    clip.write_bytes(FAKE_MP4)
    assert matching_omni_clip(videos, still) == clip


def test_file_id_from_uri():
    assert file_id_from_uri("files/abc-123") == "abc-123"
    assert (
        file_id_from_uri(
            "https://generativelanguage.googleapis.com/v1beta/files/abc-123:download?alt=media"
        )
        == "abc-123"
    )


def test_generate_video_reads_inline_mp4():
    captured: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        captured["body"] = body
        captured["url"] = str(request.url)
        assert request.headers["x-goog-api-key"] == "test-key"
        assert body["model"] == GEMINI_OMNI_VIDEO_MODEL
        assert body["generation_config"]["video_config"]["task"] == "image_to_video"
        assert body["response_format"]["type"] == "video"
        assert body["response_format"]["resolution"] == "720p"
        assert body["input"][0]["type"] == "image"
        assert body["input"][1]["type"] == "text"
        return httpx.Response(200, json=_inline_payload())

    client = httpx.Client(transport=httpx.MockTransport(handler))
    result = generate_video(
        "Animate this still for about 5 seconds.",
        tiny_png(),
        api_key="test-key",
        client=client,
        duration_seconds=5,
    )
    assert result.data == FAKE_MP4
    assert "interactions" in captured["url"]
    assert result.cost_usd > 0


def test_generate_video_downloads_uri():
    def handler(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        if request.method == "POST" and url.rstrip("/").endswith("/interactions"):
            return httpx.Response(
                200,
                json={
                    "id": "v1_uri",
                    "status": "completed",
                    "steps": [
                        {
                            "type": "model_output",
                            "content": [
                                {
                                    "type": "video",
                                    "mime_type": "video/mp4",
                                    "uri": "files/abc-123",
                                }
                            ],
                        }
                    ],
                },
            )
        if request.method == "GET" and "/files/abc-123" in url and ":download" not in url:
            return httpx.Response(
                200, json={"name": "files/abc-123", "state": "ACTIVE"}
            )
        if request.method == "GET" and ":download" in url:
            return httpx.Response(200, content=FAKE_MP4)
        return httpx.Response(404, text=url)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    result = generate_video(
        "Animate this still.",
        tiny_png(),
        api_key="test-key",
        client=client,
    )
    assert result.data == FAKE_MP4


def test_generate_video_requires_key_and_still():
    with pytest.raises(GeminiOmniError, match="GEMINI_API_KEY"):
        generate_video("prompt", tiny_png(), api_key="")
    with pytest.raises(GeminiOmniError, match="source still"):
        generate_video("prompt", b"", api_key="test-key")


def test_adapter_rejects_empty_still():
    import asyncio

    adapter = GeminiOmniVideoAdapter(api_key="test-key")

    async def _run() -> None:
        await adapter.generate_clip("", "move", 4.0, GEMINI_OMNI_VIDEO_MODEL)

    with pytest.raises(ValueError, match="source_still_url"):
        asyncio.run(_run())


def _ready_job(tmp_path: Path, *, ready: bool = True) -> tuple[str, Path]:
    job_id = "omni-flash__test__aaa"
    dest = ensure_job_tree(job_id, root=tmp_path)
    manifest = GenerationManifest(
        job_id=job_id,
        created_at="2026-09-19T00:00:00+00:00",
        channel_mode="how_they_took_over",
        title="How Nvidia Took Over AI",
        slug="nvidia-took-over-ai",
        state=JobState.images_ingested,
        qa={"ready_to_publish": ready, "originality_score": 88},
    )
    write_manifest(manifest, root=tmp_path)
    jobs = dest / "fixtures" / "nvidia-took-over-ai_v1_image_jobs.json"
    jobs.write_text(
        json.dumps(
            {
                "jobs": [
                    {
                        "id": "000",
                        "filename": "000_00-00-00.png",
                        "generate_filename": "sdeadbeef_000.png",
                        "aspect": "16:9",
                        "prompt": "stick-figure doodle of two graphics cards on a board",
                        "camera_motion": "slow push-in",
                    }
                ]
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (dest / "timestamps.json").write_text(
        json.dumps(
            {
                "scene_count": 1,
                "scenes": [
                    {
                        "index": 0,
                        "start": 0.0,
                        "end": 8.0,
                        "filename": "000_00-00-00.png",
                        "text": "two cards",
                    }
                ],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    still = dest / "images" / "000_00-00-00.png"
    still.write_bytes(tiny_png())
    return job_id, dest


def test_generate_job_videos_writes_mp4(tmp_path: Path):
    job_id, dest = _ready_job(tmp_path)
    calls: list[str] = []

    def fake(prompt: str, still: bytes, **kwargs):
        calls.append(prompt)
        from adapters.video_gen.gemini_omni import GeminiOmniVideoResult

        assert still
        assert kwargs["duration_seconds"] == 8.0
        return GeminiOmniVideoResult(
            data=FAKE_MP4, cost_usd=0.81, duration_seconds=8.0
        )

    result = generate_job_videos(
        job_id,
        artifacts_root=tmp_path,
        generate=fake,
        api_key="unused",
    )
    clip = dest / "videos" / "000_00-00-00.mp4"
    assert clip.is_file()
    assert clip.read_bytes() == FAKE_MP4
    assert result["generated"] == 1
    assert "about 8 seconds" in calls[0]
    assert "slow push-in" in calls[0]
    ledger = json.loads((dest / "videos" / "ledger.json").read_text())
    assert ledger["model"] == GEMINI_OMNI_VIDEO_MODEL
    assert ledger["public_name"] == "Omni 1.1 Flash"


def test_generate_job_videos_skips_existing(tmp_path: Path):
    job_id, dest = _ready_job(tmp_path)
    existing = dest / "videos" / "000_00-00-00.mp4"
    existing.parent.mkdir(parents=True, exist_ok=True)
    existing.write_bytes(b"old-clip")
    calls: list[str] = []

    def fake(prompt: str, still: bytes, **kwargs):
        calls.append(prompt)
        from adapters.video_gen.gemini_omni import GeminiOmniVideoResult

        return GeminiOmniVideoResult(data=FAKE_MP4)

    result = generate_job_videos(
        job_id,
        artifacts_root=tmp_path,
        generate=fake,
        api_key="unused",
    )
    assert result["skipped"] == 1
    assert result["generated"] == 0
    assert calls == []
    assert existing.read_bytes() == b"old-clip"


def test_generate_job_videos_blocks_without_qa(tmp_path: Path):
    job_id, _dest = _ready_job(tmp_path, ready=False)
    with pytest.raises(GeminiVideosError, match="ready_to_publish"):
        generate_job_videos(
            job_id,
            artifacts_root=tmp_path,
            generate=lambda prompt, still, **kwargs: (_ for _ in ()).throw(
                AssertionError()
            ),
            api_key="unused",
        )


def test_generate_job_videos_dry_run(tmp_path: Path):
    job_id, dest = _ready_job(tmp_path)
    result = generate_job_videos(
        job_id,
        artifacts_root=tmp_path,
        dry_run=True,
        api_key="",
    )
    assert result["dry_run"] is True
    assert result["generated"] == 0
    assert not (dest / "videos" / "000_00-00-00.mp4").is_file()


def test_generate_job_videos_missing_still(tmp_path: Path):
    job_id, dest = _ready_job(tmp_path)
    (dest / "images" / "000_00-00-00.png").unlink()
    result = generate_job_videos(
        job_id,
        artifacts_root=tmp_path,
        generate=lambda prompt, still, **kwargs: (_ for _ in ()).throw(
            AssertionError()
        ),
        api_key="unused",
    )
    assert result["missing_stills"] == 1
    assert result["generated"] == 0


def test_videos_cli_help_and_operator_notes(tmp_path: Path):
    job_id, _dest = _ready_job(tmp_path)
    from channel.job import load_manifest, write_operator_md

    manifest = load_manifest(job_id, root=tmp_path)
    text = write_operator_md(manifest, root=tmp_path).read_text(encoding="utf-8")
    assert "python -m channel videos" in text
    assert "gemini-omni-1.1-flash" in text
    from channel.__main__ import main

    with pytest.raises(SystemExit) as excinfo:
        main(["videos", "--help"])
    assert excinfo.value.code == 0
