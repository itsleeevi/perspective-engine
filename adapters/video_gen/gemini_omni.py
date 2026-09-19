"""
Gemini Omni 1.1 Flash adapter — image-to-video.

Public name: Omni 1.1 Flash. Model id: ``gemini-omni-1.1-flash``.
REST: POST ``/v1beta/interactions`` (not generateContent). Video is 3–10 s
at 24 fps. Duration has no documented API field — clamp and put it in the
prompt. Default 720p (~$0.10/s). URI delivery for clips over 4 MB.

Graph path: ``GeminiOmniVideoAdapter`` via ``--video-provider gemini-omni-1.1-flash``
(aliases ``omi-1.1-flash``, ``omni-1.1-flash``). Documentary path:
``python -m channel videos``. Uses ``GEMINI_API_KEY`` (same key as Gemini TTS
and Nano Banana 2). Does not call Seedance, fal.ai, or Google Flow. Still-first:
a source still is required. Does not run on ``--resume``.
"""

from __future__ import annotations

import asyncio
import base64
import hashlib
import os
import random
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

import httpx

from adapters import _cache, pricing
from adapters.image_gen.gemini import mime_for, read_local_image
from adapters.video_gen.base import VideoGenAdapter, VideoGenResult
from graph.assets import save_asset

GEMINI_OMNI_VIDEO_MODEL = "gemini-omni-1.1-flash"
GEMINI_OMNI_VIDEO_PUBLIC_NAME = "Omni 1.1 Flash"
GEMINI_OMNI_ASPECTS = ("16:9", "9:16")
GEMINI_OMNI_RESOLUTIONS = ("360p", "720p", "1080p", "4k")
GEMINI_OMNI_DEFAULT_ASPECT = "16:9"
GEMINI_OMNI_DEFAULT_RESOLUTION = "720p"
GEMINI_OMNI_MIN_SECONDS = 3.0
GEMINI_OMNI_MAX_SECONDS = 10.0
GEMINI_OMNI_ALIASES = frozenset(
    {
        "gemini-omni-1.1-flash",
        "omi-1.1-flash",
        "omni-1.1-flash",
        "omni",
    }
)

_INTERACTIONS_URL = "https://generativelanguage.googleapis.com/v1beta/interactions"
_FILES_URL = "https://generativelanguage.googleapis.com/v1beta/files"
_DOWNLOAD_URL = "https://generativelanguage.googleapis.com/download/v1beta/files"
_MAX_RETRIES = 6
_RETRY_BASE_SECONDS = 2.0
_RETRY_MAX_SECONDS = 60.0
_TIMEOUT = 600.0
_POLL_SECONDS = 5.0
_POLL_TIMEOUT = 600.0
_FILE_ID_RE = re.compile(r"files/([^/:?]+)")


class GeminiOmniError(RuntimeError):
    """Omni 1.1 Flash / Gemini video generation failed. Do not swap providers."""


@dataclass
class GeminiOmniVideoResult:
    """One generated clip plus billed usage."""

    data: bytes
    mime: str = "video/mp4"
    cost_usd: float = 0.0
    duration_seconds: float = GEMINI_OMNI_MIN_SECONDS
    usage: dict[str, Any] = field(default_factory=dict)
    interaction_id: str = ""


def gemini_omni_api_key() -> str:
    return (
        os.environ.get("GEMINI_API_KEY", "").strip()
        or os.environ.get("GOOGLE_API_KEY", "").strip()
        or os.environ.get("GOOGLE_GENAI_API_KEY", "").strip()
    )


def clamp_omni_duration(seconds: float) -> float:
    """Omni clips are 3–10 seconds. No documented duration API field."""
    try:
        value = float(seconds)
    except (TypeError, ValueError):
        value = GEMINI_OMNI_MIN_SECONDS
    if value != value:  # NaN
        value = GEMINI_OMNI_MIN_SECONDS
    return max(GEMINI_OMNI_MIN_SECONDS, min(GEMINI_OMNI_MAX_SECONDS, value))


def omni_motion_prompt(
    scene_prompt: str,
    duration_seconds: float,
    camera: str = "",
) -> str:
    """Prompt that keeps the still's drawn look and asks for a timed clip."""
    duration = clamp_omni_duration(duration_seconds)
    bits = [
        f"Animate this still for about {duration:.0f} seconds.",
        "Keep the exact drawn look, faces, clothes, colors, and staging.",
        "Do not add readable text, logos, or photoreal texture.",
        "Subtle natural motion only. Do not change the character design.",
    ]
    cam = (camera or "").strip()
    if cam and cam.lower() not in {"static", "none"}:
        bits.append(f"Camera: {cam}.")
    extra = (scene_prompt or "").strip()
    if extra:
        bits.append(extra)
    return " ".join(bits)


def matching_omni_clip(videos_dir: Path, still: Path) -> Path | None:
    """Return ``videos/{still.stem}.mp4`` when a clip was generated for that still."""
    if not videos_dir.is_dir():
        return None
    stem = still.stem
    for ext in (".mp4", ".webm", ".mov"):
        candidate = videos_dir / f"{stem}{ext}"
        if candidate.is_file() and candidate.stat().st_size > 0:
            return candidate
    return None


def _headers(api_key: str) -> dict[str, str]:
    return {
        "Content-Type": "application/json",
        "x-goog-api-key": api_key,
    }


def _normalize_resolution(resolution: str) -> str:
    raw = (resolution or GEMINI_OMNI_DEFAULT_RESOLUTION).strip()
    if raw == "4K":
        raw = "4k"
    if raw not in GEMINI_OMNI_RESOLUTIONS:
        raise GeminiOmniError(
            f"unsupported resolution {resolution!r}; need one of {GEMINI_OMNI_RESOLUTIONS}"
        )
    return raw


def _normalize_aspect(aspect_ratio: str) -> str:
    raw = (aspect_ratio or GEMINI_OMNI_DEFAULT_ASPECT).strip()
    if raw not in GEMINI_OMNI_ASPECTS:
        raise GeminiOmniError(
            f"unsupported aspect ratio {aspect_ratio!r}; need one of {GEMINI_OMNI_ASPECTS}"
        )
    return raw


def _num(mapping: dict[str, Any], *keys: str) -> int:
    for key in keys:
        if key in mapping and mapping[key] is not None:
            try:
                return int(mapping[key])
            except (TypeError, ValueError):
                continue
    return 0


def _status(payload: dict[str, Any]) -> str:
    return str(
        payload.get("status") or payload.get("state") or ""
    ).strip().lower()


def _interaction_id(payload: dict[str, Any]) -> str:
    raw = payload.get("id") or payload.get("name") or ""
    text = str(raw).strip()
    if text.startswith("interactions/"):
        return text.split("/", 1)[1]
    return text


def _video_items(payload: dict[str, Any]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for key in ("output_video", "outputVideo"):
        blob = payload.get(key)
        if isinstance(blob, dict):
            items.append(blob)
    for key in ("output", "outputs"):
        for blob in payload.get(key) or []:
            if isinstance(blob, dict) and str(blob.get("type") or "") == "video":
                items.append(blob)
    for step in payload.get("steps") or []:
        if not isinstance(step, dict):
            continue
        step_type = str(step.get("type") or "")
        if step_type and step_type not in {"model_output", "output", "message"}:
            continue
        for blob in step.get("content") or []:
            if isinstance(blob, dict) and str(blob.get("type") or "") == "video":
                items.append(blob)
    return items


def _video_bytes(item: dict[str, Any]) -> bytes | None:
    data = item.get("data") or item.get("video_data") or ""
    if not data:
        inline = item.get("inlineData") or item.get("inline_data") or {}
        if isinstance(inline, dict):
            data = inline.get("data") or ""
    if not data or not isinstance(data, str):
        return None
    try:
        return base64.b64decode(data)
    except (ValueError, TypeError):
        return None


def _video_uri(item: dict[str, Any]) -> str:
    for key in ("uri", "url", "file_uri", "fileUri", "download_uri", "downloadUri"):
        value = item.get(key)
        if value:
            return str(value).strip()
    file_obj = item.get("file") or item.get("fileData") or item.get("file_data") or {}
    if isinstance(file_obj, dict):
        for key in ("uri", "url", "name", "fileUri"):
            value = file_obj.get(key)
            if value:
                return str(value).strip()
    return ""


def _video_mime(item: dict[str, Any]) -> str:
    return str(
        item.get("mime_type")
        or item.get("mimeType")
        or "video/mp4"
    )


def file_id_from_uri(uri: str) -> str:
    match = _FILE_ID_RE.search(uri or "")
    if not match:
        raise GeminiOmniError(f"Omni video URI had no files/ id: {uri!r}")
    return match.group(1)


def usage_cost(
    payload: dict[str, Any],
    *,
    resolution: str,
    duration_seconds: float,
) -> tuple[float, dict[str, Any]]:
    """Bill from API usage when present, else resolution × duration floor."""
    usage = payload.get("usage") or payload.get("usageMetadata") or {}
    if not isinstance(usage, dict):
        usage = {}
    details_in = usage.get("promptTokensDetails") or usage.get("prompt_tokens_details") or []
    details_out = (
        usage.get("candidatesTokensDetails")
        or usage.get("candidates_tokens_details")
        or usage.get("output_tokens_details")
        or []
    )
    text_in = image_in = video_in = 0
    for row in details_in:
        if not isinstance(row, dict):
            continue
        modality = str(row.get("modality") or "").upper()
        count = _num(row, "tokenCount", "token_count")
        if modality == "IMAGE":
            image_in += count
        elif modality == "VIDEO":
            video_in += count
        else:
            text_in += count
    text_out = video_out = 0
    for row in details_out:
        if not isinstance(row, dict):
            continue
        modality = str(row.get("modality") or "").upper()
        count = _num(row, "tokenCount", "token_count")
        if modality == "VIDEO":
            video_out += count
        else:
            text_out += count
    if not details_in:
        text_in = _num(usage, "input_tokens", "promptTokenCount", "prompt_token_count")
        image_in = _num(usage, "image_input_tokens")
        video_in = _num(usage, "video_input_tokens")
    if not details_out:
        video_out = _num(
            usage,
            "video_output_tokens",
            "output_tokens",
            "candidatesTokenCount",
            "candidates_token_count",
        )
        text_out = _num(usage, "text_output_tokens")
    summary = {
        "text_input_tokens": text_in,
        "image_input_tokens": image_in,
        "video_input_tokens": video_in,
        "text_output_tokens": text_out,
        "video_output_tokens": video_out,
        "resolution": resolution,
        "duration_seconds": duration_seconds,
    }
    if video_out or text_in or image_in or video_in or text_out:
        cost = pricing.gemini_omni_video_cost(
            text_in, image_in, video_in, text_out, video_out
        )
        return cost, summary
    cost = pricing.gemini_omni_video_floor_cost(resolution, duration_seconds)
    summary["video_output_tokens"] = int(
        round(
            pricing.GEMINI_OMNI_VIDEO_TOKENS_PER_SECOND.get(
                resolution, pricing.GEMINI_OMNI_VIDEO_TOKENS_PER_SECOND["720p"]
            )
            * duration_seconds
        )
    )
    return cost, summary


def _request_body(
    *,
    model: str,
    still: bytes,
    mime: str,
    prompt: str,
    aspect_ratio: str,
    resolution: str,
) -> dict[str, Any]:
    return {
        "model": model,
        "input": [
            {
                "type": "image",
                "data": base64.b64encode(still).decode("ascii"),
                "mime_type": mime or "image/png",
            },
            {"type": "text", "text": prompt},
        ],
        "generation_config": {
            "video_config": {
                "task": "image_to_video",
            }
        },
        "response_format": {
            "type": "video",
            "aspect_ratio": aspect_ratio,
            "resolution": resolution,
            "delivery": "uri",
        },
    }


def _poll_interaction(
    http: httpx.Client,
    api_key: str,
    interaction_id: str,
    *,
    timeout: float = _POLL_TIMEOUT,
) -> dict[str, Any]:
    deadline = time.monotonic() + timeout
    url = f"{_INTERACTIONS_URL}/{interaction_id}"
    headers = _headers(api_key)
    last: dict[str, Any] = {}
    while time.monotonic() < deadline:
        response = http.get(url, headers=headers)
        if response.status_code in {429, 500, 503}:
            time.sleep(_POLL_SECONDS)
            continue
        if response.status_code >= 400:
            raise GeminiOmniError(
                f"Omni interaction poll failed HTTP {response.status_code}: "
                f"{response.text[:800]}"
            )
        last = response.json()
        status = _status(last)
        if status in {"completed", "succeeded", "success", ""}:
            if _video_items(last) or status in {"completed", "succeeded", "success"}:
                return last
        if status in {"failed", "cancelled", "canceled", "error"}:
            raise GeminiOmniError(f"Omni interaction {status}: {last!r}")
        time.sleep(_POLL_SECONDS)
    raise GeminiOmniError(
        f"Omni interaction {interaction_id} did not finish within {timeout:.0f}s"
    )


def _download_file_video(
    http: httpx.Client,
    api_key: str,
    uri: str,
    *,
    timeout: float = _POLL_TIMEOUT,
) -> bytes:
    headers = {"x-goog-api-key": api_key}
    if ":download" in uri or "alt=media" in uri:
        response = http.get(uri, headers=headers)
        if response.status_code >= 400:
            raise GeminiOmniError(
                f"Omni video download failed HTTP {response.status_code}: "
                f"{response.text[:800]}"
            )
        if not response.content:
            raise GeminiOmniError("Omni video download was empty")
        return response.content

    file_id = file_id_from_uri(uri)
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        meta = http.get(f"{_FILES_URL}/{file_id}", headers=headers)
        if meta.status_code in {429, 500, 503}:
            time.sleep(_POLL_SECONDS)
            continue
        if meta.status_code >= 400:
            raise GeminiOmniError(
                f"Omni files poll failed HTTP {meta.status_code}: {meta.text[:800]}"
            )
        payload = meta.json()
        state = str(payload.get("state") or payload.get("status") or "").upper()
        if state in {"ACTIVE", "SUCCEEDED", "READY", ""}:
            break
        if state in {"FAILED", "ERROR"}:
            raise GeminiOmniError(f"Omni file {file_id} {state}: {payload!r}")
        time.sleep(_POLL_SECONDS)
    else:
        raise GeminiOmniError(f"Omni file {file_id} did not become ACTIVE")

    download = http.get(
        f"{_FILES_URL}/{file_id}:download",
        params={"alt": "media"},
        headers=headers,
    )
    if download.status_code >= 400:
        download = http.get(
            f"{_DOWNLOAD_URL}/{file_id}:download",
            params={"alt": "media"},
            headers=headers,
        )
    if download.status_code >= 400:
        raise GeminiOmniError(
            f"Omni video download failed HTTP {download.status_code}: "
            f"{download.text[:800]}"
        )
    if not download.content:
        raise GeminiOmniError("Omni video download was empty")
    return download.content


def _extract_video(
    http: httpx.Client,
    api_key: str,
    payload: dict[str, Any],
) -> tuple[bytes, str]:
    items = _video_items(payload)
    if not items:
        err = payload.get("error") or payload.get("status") or payload
        raise GeminiOmniError(f"Omni response had no video: {err!r}")
    last_error = ""
    for item in items:
        data = _video_bytes(item)
        if data:
            return data, _video_mime(item)
        uri = _video_uri(item)
        if not uri:
            continue
        try:
            return _download_file_video(http, api_key, uri), _video_mime(item)
        except GeminiOmniError as exc:
            last_error = str(exc)
    raise GeminiOmniError(last_error or f"Omni response had no video bytes: {payload!r}")


def generate_video(
    prompt: str,
    still: bytes,
    *,
    api_key: str,
    mime: str = "image/png",
    model: str = GEMINI_OMNI_VIDEO_MODEL,
    aspect_ratio: str = GEMINI_OMNI_DEFAULT_ASPECT,
    resolution: str = GEMINI_OMNI_DEFAULT_RESOLUTION,
    duration_seconds: float = GEMINI_OMNI_MIN_SECONDS,
    client: httpx.Client | None = None,
    timeout: float = _TIMEOUT,
    retries: int = _MAX_RETRIES,
) -> GeminiOmniVideoResult:
    """Call Omni 1.1 Flash image-to-video and return MP4 bytes.

    ``still`` is required. Empty prompt, missing key, or missing still fail
    closed — no provider swap to Seedance / fal / Flow.
    """
    if not api_key:
        raise GeminiOmniError(
            "GEMINI_API_KEY (or GOOGLE_API_KEY) is missing. "
            "Assemble still holds remain the default. "
            "Do not fall back to Seedance, fal.ai, or Google Flow."
        )
    if not still:
        raise GeminiOmniError(
            "Omni image-to-video requires a source still. Still-first: do not "
            "call text-to-video."
        )
    text = (prompt or "").strip()
    if not text:
        raise GeminiOmniError("empty video prompt")
    aspect = _normalize_aspect(aspect_ratio)
    reso = _normalize_resolution(resolution)
    duration = clamp_omni_duration(duration_seconds)
    body = _request_body(
        model=model,
        still=still,
        mime=mime,
        prompt=text,
        aspect_ratio=aspect,
        resolution=reso,
    )
    headers = _headers(api_key)
    own_client = client is None
    http = client or httpx.Client(timeout=timeout)
    last_error = ""
    try:
        delay = _RETRY_BASE_SECONDS
        payload: dict[str, Any] | None = None
        for attempt in range(retries):
            response = http.post(_INTERACTIONS_URL, headers=headers, json=body)
            if response.status_code in {429, 500, 503} and attempt + 1 < retries:
                last_error = response.text[:800]
                time.sleep(delay + random.uniform(0, 0.5))
                delay = min(delay * 2, _RETRY_MAX_SECONDS)
                continue
            if response.status_code >= 400:
                raise GeminiOmniError(
                    f"Omni video HTTP {response.status_code}: {response.text[:800]}"
                )
            payload = response.json()
            break
        if payload is None:
            raise GeminiOmniError(
                f"Omni video failed after retries: {last_error or 'no response'}"
            )
        status = _status(payload)
        interaction_id = _interaction_id(payload)
        if status in {"in_progress", "pending", "processing", "running"} or (
            interaction_id and not _video_items(payload) and status not in {
                "completed", "succeeded", "success", "failed",
            }
        ):
            if not interaction_id:
                raise GeminiOmniError(f"Omni interaction had no id: {payload!r}")
            payload = _poll_interaction(http, api_key, interaction_id)
            interaction_id = _interaction_id(payload) or interaction_id
        if _status(payload) in {"failed", "cancelled", "canceled", "error"}:
            raise GeminiOmniError(f"Omni interaction failed: {payload!r}")
        data, out_mime = _extract_video(http, api_key, payload)
        cost, usage = usage_cost(
            payload, resolution=reso, duration_seconds=duration
        )
        return GeminiOmniVideoResult(
            data=data,
            mime=out_mime or "video/mp4",
            cost_usd=cost,
            duration_seconds=duration,
            usage=usage,
            interaction_id=interaction_id,
        )
    finally:
        if own_client:
            http.close()


def load_still_bytes(
    url_or_path: str,
    *,
    client: httpx.Client | None = None,
) -> tuple[bytes, str]:
    """Load a still from a local path, file:// URL, or https URL."""
    local = read_local_image(url_or_path)
    if local is not None:
        return local
    raw = (url_or_path or "").strip()
    if raw.startswith("http://") or raw.startswith("https://"):
        own = client is None
        http = client or httpx.Client(timeout=60.0)
        try:
            response = http.get(raw)
            if response.status_code >= 400 or not response.content:
                raise GeminiOmniError(
                    f"could not download source still {raw!r} "
                    f"(HTTP {response.status_code})"
                )
            mime = (response.headers.get("content-type") or "image/png").split(";")[0]
            return response.content, mime or "image/png"
        finally:
            if own:
                http.close()
    if raw.startswith("file:"):
        path = Path(unquote(urlparse(raw).path))
        if path.is_file():
            return path.read_bytes(), mime_for(path)
    raise GeminiOmniError(
        f"Omni image-to-video requires a readable source still, got {url_or_path!r}"
    )


class GeminiOmniVideoAdapter(VideoGenAdapter):
    """Graph adapter: still-first Omni 1.1 Flash image-to-video."""

    def __init__(
        self,
        *,
        model: str = GEMINI_OMNI_VIDEO_MODEL,
        resolution: str = GEMINI_OMNI_DEFAULT_RESOLUTION,
        aspect_ratio: str = GEMINI_OMNI_DEFAULT_ASPECT,
        api_key: str | None = None,
    ) -> None:
        self.model = model
        self.resolution = resolution
        self.aspect_ratio = aspect_ratio
        self.api_key = api_key

    async def generate_clip(
        self,
        source_still_url: str,
        prompt: str,
        duration_seconds: float,
        model: str,
    ) -> VideoGenResult:
        if not source_still_url:
            raise ValueError(
                "GeminiOmniVideoAdapter.generate_clip requires a non-empty "
                "source_still_url. A derived still must be provided before "
                "video generation."
            )
        duration = clamp_omni_duration(duration_seconds)
        endpoint = (
            model
            if model and "omni" in model
            else self.model
        )
        still, mime = load_still_bytes(source_still_url)
        motion = omni_motion_prompt(prompt, duration)
        cache_key = _cache.make_key(
            {
                "model": endpoint,
                "prompt": motion,
                "still_sha": hashlib.sha1(still).hexdigest(),
                "duration": duration,
                "resolution": self.resolution,
                "aspect": self.aspect_ratio,
            }
        )
        cached = _cache.load("omni_clip", cache_key)
        if cached is not None:
            return VideoGenResult(
                clip_url=cached["clip_url"],
                duration_seconds=cached["duration_seconds"],
                cost_usd=0.0,
            )
        key = self.api_key if self.api_key is not None else gemini_omni_api_key()
        result = await asyncio.to_thread(
            generate_video,
            motion,
            still,
            api_key=key,
            mime=mime,
            model=endpoint,
            aspect_ratio=self.aspect_ratio,
            resolution=self.resolution,
            duration_seconds=duration,
        )
        digest = hashlib.sha1(result.data).hexdigest()[:12]
        clip_url = save_asset(f"omni_clips/{digest}.mp4", result.data)
        _cache.store(
            "omni_clip",
            cache_key,
            {"clip_url": clip_url, "duration_seconds": result.duration_seconds},
        )
        return VideoGenResult(
            clip_url=clip_url,
            duration_seconds=result.duration_seconds,
            cost_usd=result.cost_usd,
        )
