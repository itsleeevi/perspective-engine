"""Pinned versions for the YouTube documentary engine.

Normal generation jobs treat this file as READ-ONLY.
Pipeline reproducibility is the goal. External image/TTS models are not
byte-identical across runs; quality, style, structure, and config must match.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from channel.modes import ChannelMode

VIDEO_ENGINE_VERSION = "2026.08.25"
PROMPT_VERSION = "2026.08.25"
VISUAL_STYLE_VERSION = "2026.08.25"

# Documentary path only. Do not silently swap these.
MODEL_LOCK = {
    "title_analysis": "channel.title.analyze_title (deterministic code)",
    "research_seed": "wikipedia_api_extract",
    "research": "cursor_grok_agent + channel.*_prompts.RESEARCHER",
    "fact_check": "channel.factcheck (deterministic code) + agent review",
    "story": "cursor_grok_agent + channel.*_prompts.STORY_ARCHITECT",
    "narration": "cursor_grok_agent + channel.*_prompts.NARRATION_WRITER",
    "scenes": "cursor_grok_agent + channel.*_prompts.SCENE_BREAKDOWN",
    "image": "cursor_grok_GenerateImage",
    "tts": "kokoro",
    "thumbnail": "cursor_grok_GenerateImage + channel.youtube overlay",
    "short": "channel.shorts + kokoro + ffmpeg",
    "qa": "channel.qa + originality + monetization_qa + channel.quality_bar",
}

# Channel documentary path forbids these. Missing Kokoro/GenerateImage = stop.
FORBIDDEN_FALLBACKS = (
    "edge-tts",
    "elevenlabs",
    "fal image",
    "openai image",
    "pollinations",
    "latest",
    "auto",
)

RENDER_LOCK = {
    "long_aspect": "16:9",
    "long_output": "3840x2160",
    "still_ingest": "1280x720 cover-crop then upscale",
    "short_output": "1080x1920",
    "youtube_thumb": "1280x720 jpeg",
    "youtube_short_thumb": "1080x1920 jpeg",
    "fps": 30,
    "video_codec": "libx264",
    "crf": 20,
    "preset": "veryfast",
    "pix_fmt": "yuv420p",
    "profile": "high",
    "gop": 60,
    "audio": "whisper-forced-aligned + ffmpeg",
}

KOKORO_LOCK = {
    "provider": "kokoro",
    "default_voice": "am_liam",
    "roster": ("am_liam", "am_michael", "am_fenrir"),
    "new_title_speed_min": 1.0,
    "default_speed": 1.15,
}

PROMPT_MODULES = {
    ChannelMode.what_they_really_think: "channel.agent_prompts",
    ChannelMode.behind_the_business: "channel.business_prompts",
    ChannelMode.how_they_took_over: "channel.takeover_prompts",
}

IMAGE_FILENAME_RULE = (
    "Never put a company, product, or person name in a GenerateImage "
    "filename. The image model paints that word onto cards, awnings, and "
    "signs. Call GenerateImage with the job's generate_filename "
    "(hashed token, not the slug), then copy onto filename / copy_to "
    "for assemble."
)


def image_token_for(slug: str, job_id: str | None = None) -> str:
    """Hex token with no English words. Unique per job_id, stable per slug."""
    return hashlib.sha1((job_id or slug).encode("utf-8")).hexdigest()[:8]


def generate_image_filename(
    index: int = 0,
    *,
    token: str,
    kind: str = "scene",
) -> str:
    """Neutral GenerateImage name. Parallel jobs must not share this string."""
    cleaned = "".join(c for c in token.lower() if c in "0123456789abcdef")
    if len(cleaned) < 4:
        cleaned = hashlib.sha1(token.encode("utf-8")).hexdigest()[:8]
    if kind == "scene":
        return f"s{cleaned}_{index:03d}.png"
    if kind == "short_scene":
        return f"v{cleaned}_{index:03d}.png"
    if kind == "thumb":
        return f"t{cleaned}.png"
    if kind == "short_thumb":
        return f"u{cleaned}.png"
    raise ValueError(f"unknown generate-image kind {kind!r}")


def generate_name_map(jobs_file: Path) -> dict[str, str]:
    """Map assemble destination filename → GenerateImage filename."""
    if not jobs_file.is_file():
        return {}
    data = json.loads(jobs_file.read_text(encoding="utf-8"))
    out: dict[str, str] = {}
    for job in data.get("jobs") or []:
        dest = str(job.get("filename") or "")
        gen = str(job.get("generate_filename") or "")
        if dest and gen:
            out[dest] = gen
    return out

NETWORK_DOMAINS = (
    "en.wikipedia.org",  # research seed only
    "sec.gov",  # filings (agent browser)
    "cursor.com",  # GenerateImage
)

NO_PROVIDER_FALLBACK = True
