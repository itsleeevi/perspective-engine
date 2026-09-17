"""Nano Banana 2 (gemini-3.1-flash-image) stills: HTTP client + job runner."""

from __future__ import annotations

import base64
import io
import json
from pathlib import Path

import httpx
import pytest
from PIL import Image

from adapters.image_gen.gemini import (
    GEMINI_IMAGE_MODEL,
    GeminiImageError,
    GeminiImageGenAdapter,
    generate_image,
    usage_cost,
)
from adapters.pricing import gemini_flash_image_cost, gemini_flash_image_size_cost
from channel.gemini_images import GeminiImagesError, generate_job_images
from channel.job import (
    GenerationManifest,
    JobState,
    ensure_job_tree,
    write_manifest,
)


def tiny_png(color: tuple[int, int, int] = (20, 40, 80)) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (32, 18), color).save(buf, format="PNG")
    return buf.getvalue()


def _payload(png: bytes | None = None) -> dict:
    data = png if png is not None else tiny_png()
    return {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {"text": "ok"},
                        {
                            "inlineData": {
                                "mimeType": "image/png",
                                "data": base64.b64encode(data).decode("ascii"),
                            }
                        },
                    ]
                }
            }
        ],
        "usageMetadata": {
            "promptTokenCount": 100,
            "thoughtsTokenCount": 20,
            "promptTokensDetails": [
                {"modality": "TEXT", "tokenCount": 80},
                {"modality": "IMAGE", "tokenCount": 1120},
            ],
            "candidatesTokensDetails": [
                {"modality": "TEXT", "tokenCount": 10},
                {"modality": "IMAGE", "tokenCount": 1680},
            ],
        },
    }


def test_wait_images_operator_mentions_nano_banana(tmp_path: Path):
    job_id, _dest = _ready_job(tmp_path)
    from channel.job import load_manifest, write_operator_md

    manifest = load_manifest(job_id, root=tmp_path)
    path = write_operator_md(manifest, root=tmp_path)
    text = path.read_text(encoding="utf-8")
    assert "python -m channel images" in text
    assert "gemini-3.1-flash-image" in text
    assert "Google Flow" in text
    from channel.__main__ import main

    with pytest.raises(SystemExit) as excinfo:
        main(["images", "--help"])
    assert excinfo.value.code == 0
    assert round(gemini_flash_image_size_cost("2K"), 3) == 0.101
    assert round(gemini_flash_image_size_cost("4K"), 3) == 0.151
    mixed = gemini_flash_image_cost(80, 1120, 30, 1680)
    assert mixed > gemini_flash_image_size_cost("2K")


def test_usage_cost_falls_back_to_size_tokens():
    cost, summary = usage_cost({}, "2K")
    assert summary["image_output_tokens"] == 1680
    assert cost == gemini_flash_image_size_cost("2K")


def test_generate_image_reads_inline_png():
    png = tiny_png((9, 8, 7))
    captured: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        captured["body"] = body
        captured["url"] = str(request.url)
        assert request.headers["x-goog-api-key"] == "test-key"
        return httpx.Response(200, json=_payload(png))

    client = httpx.Client(transport=httpx.MockTransport(handler))
    result = generate_image(
        "A stick-figure doodle of a board.",
        api_key="test-key",
        client=client,
        aspect_ratio="16:9",
        image_size="2K",
    )
    assert result.data == png
    assert "gemini-3.1-flash-image" in captured["url"]
    config = captured["body"]["generationConfig"]
    assert config["responseModalities"] == ["TEXT", "IMAGE"]
    assert config["imageConfig"]["aspectRatio"] == "16:9"
    assert config["imageConfig"]["imageSize"] == "2K"
    assert config["responseFormat"]["image"]["imageSize"] == "2K"
    assert captured["body"]["contents"][0]["parts"][0]["text"].startswith("A stick-figure")
    assert result.cost_usd > 0


def test_generate_image_requires_key():
    with pytest.raises(GeminiImageError, match="GEMINI_API_KEY"):
        generate_image("prompt", api_key="")


def test_generate_image_attaches_reference_bytes():
    png = tiny_png()
    ref = tiny_png((1, 2, 3))

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        parts = body["contents"][0]["parts"]
        assert parts[0]["text"]
        assert parts[1]["inlineData"]["mimeType"] == "image/png"
        assert base64.b64decode(parts[1]["inlineData"]["data"]) == ref
        return httpx.Response(200, json=_payload(png))

    client = httpx.Client(transport=httpx.MockTransport(handler))
    result = generate_image(
        "Keep this face.",
        api_key="test-key",
        client=client,
        reference_images=[(ref, "image/png")],
    )
    assert result.data == png


def _ready_job(tmp_path: Path, *, ready: bool = True) -> tuple[str, Path]:
    job_id = "nano-banana__test__aaa"
    dest = ensure_job_tree(job_id, root=tmp_path)
    manifest = GenerationManifest(
        job_id=job_id,
        created_at="2026-09-17T00:00:00+00:00",
        channel_mode="how_they_took_over",
        title="How Nvidia Took Over AI",
        slug="nvidia-took-over-ai",
        state=JobState.wait_images,
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
                        "reference_image_paths": [],
                    }
                ]
            }
        )
        + "\n",
        encoding="utf-8",
    )
    return job_id, dest


def test_generate_job_images_writes_staging_png(tmp_path: Path):
    job_id, dest = _ready_job(tmp_path)
    png = tiny_png((50, 60, 70))
    calls: list[str] = []

    def fake(prompt: str, **kwargs):
        calls.append(prompt)
        from adapters.image_gen.gemini import GeminiImageResult

        return GeminiImageResult(data=png, cost_usd=0.101, usage={"image_size": "2K"})

    result = generate_job_images(
        job_id,
        artifacts_root=tmp_path,
        generate=fake,
        api_key="unused",
        no_ingest=True,
    )
    staged = dest / "images" / "nano_banana" / "000_00-00-00.png"
    assert staged.is_file()
    assert staged.read_bytes() == png
    assert result["generated"] == 1
    assert "two graphics cards" in calls[0]
    ledger = json.loads((dest / "images" / "nano_banana" / "ledger.json").read_text())
    assert ledger["model"] == GEMINI_IMAGE_MODEL
    assert ledger["public_name"] == "Nano Banana 2"


def test_generate_job_images_skips_existing(tmp_path: Path):
    job_id, dest = _ready_job(tmp_path)
    staged = dest / "images" / "nano_banana"
    staged.mkdir(parents=True, exist_ok=True)
    existing = tiny_png((9, 9, 9))
    (staged / "000_00-00-00.png").write_bytes(existing)
    calls: list[str] = []

    def fake(prompt: str, **kwargs):
        calls.append(prompt)
        from adapters.image_gen.gemini import GeminiImageResult

        return GeminiImageResult(data=tiny_png((1, 1, 1)))

    result = generate_job_images(
        job_id,
        artifacts_root=tmp_path,
        generate=fake,
        api_key="unused",
        no_ingest=True,
    )
    assert result["skipped"] == 1
    assert result["generated"] == 0
    assert calls == []
    assert (staged / "000_00-00-00.png").read_bytes() == existing


def test_generate_job_images_blocks_without_qa(tmp_path: Path):
    job_id, _dest = _ready_job(tmp_path, ready=False)
    with pytest.raises(GeminiImagesError, match="ready_to_publish"):
        generate_job_images(
            job_id,
            artifacts_root=tmp_path,
            generate=lambda prompt, **kwargs: (_ for _ in ()).throw(AssertionError()),
            api_key="unused",
            no_ingest=True,
        )


def test_generate_job_images_dry_run(tmp_path: Path):
    job_id, dest = _ready_job(tmp_path)
    result = generate_job_images(
        job_id,
        artifacts_root=tmp_path,
        dry_run=True,
        no_ingest=True,
        api_key="",
    )
    assert result["dry_run"] is True
    assert result["generated"] == 0
    assert not (dest / "images" / "nano_banana" / "000_00-00-00.png").is_file()


@pytest.mark.asyncio
async def test_gemini_adapter_derive_still(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("ASSETS_DIR", str(tmp_path / "assets"))
    monkeypatch.setenv("ADAPTER_CACHE_DIR", str(tmp_path / "cache"))
    monkeypatch.setenv("ADAPTER_CACHE", "1")
    png = tiny_png((11, 22, 33))
    sheet = tmp_path / "sheet.png"
    sheet.write_bytes(tiny_png((4, 5, 6)))

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=_payload(png))

    client = httpx.Client(transport=httpx.MockTransport(handler))
    adapter = GeminiImageGenAdapter(api_key="test-key", client=client, image_size="2K")
    still = await adapter.derive_still(
        "wide shot of a dark room with one lamp",
        [sheet.as_uri()],
        "locked hero",
    )
    assert still.still_url.startswith("file://")
    assert still.cost_usd > 0
    cached = await adapter.derive_still(
        "wide shot of a dark room with one lamp",
        [sheet.as_uri()],
        "locked hero",
    )
    assert cached.still_url == still.still_url
    assert cached.cost_usd == 0.0
