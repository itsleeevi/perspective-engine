"""
assemble node — compose clips, stills, and audio into a real MP4.

Phase 2: downloads all fal.ai-hosted assets, converts each still to a
static video segment, concatenates segments in shot order, and mixes in
the ElevenLabs voiceover using ffmpeg. No Remotion dependency required.

Phase 3 will replace this with full Remotion rendering (captions, motion
graphics, transitions). The output contract — a local file:// MP4 path in
``final_video_path`` — is the same.
"""

from __future__ import annotations

import asyncio
import json
import re
import tempfile
from pathlib import Path

import httpx

from graph.assets import local_asset_url
from graph.state import CostEntry, PipelineState, ShotMode, ShotStatus

_FETCH_TIMEOUT = 60.0


def _slug(topic: str) -> str:
    safe = re.sub(r"[^a-z0-9]+", "_", topic.lower()).strip("_")
    return safe[:40]


async def _fetch(url: str, dest: Path) -> None:
    """Download a URL (https:// or file://) to dest."""
    if url.startswith("file://"):
        import shutil
        shutil.copy2(url.removeprefix("file://"), dest)
        return
    async with httpx.AsyncClient(timeout=_FETCH_TIMEOUT, follow_redirects=True) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        dest.write_bytes(resp.content)


async def assemble(state: PipelineState) -> dict:
    """
    Download all assets and compose a real MP4 via ffmpeg.

    Each shot becomes one segment:
      - motion shots: use the Seedance clip directly.
      - static_pan shots: freeze the FLUX still for duration_seconds.
    Segments are concatenated in shot order, then the ElevenLabs voiceover
    is mixed in (audio trimmed/padded to match total video duration).
    """
    approved = [
        s for s in state.shot_list
        if s.status in (ShotStatus.approved, ShotStatus.escalated)
    ]

    slug = _slug(state.topic)
    output_path = local_asset_url(f"output/{slug}_final.mp4")
    local_path = Path(output_path.removeprefix("file://"))
    local_path.parent.mkdir(parents=True, exist_ok=True)

    # Also write a JSON manifest for inspection.
    motion_count = sum(1 for s in approved if s.mode == ShotMode.motion)
    manifest = {
        "topic": state.topic,
        "total_shots": len(approved),
        "motion_shots": motion_count,
        "static_shots": len(approved) - motion_count,
        "voiceover_url": state.voiceover_url,
        "shots": [
            {
                "id": s.id,
                "mode": s.mode.value if hasattr(s.mode, "value") else str(s.mode),
                "status": s.status.value if hasattr(s.status, "value") else str(s.status),
                "still_url": s.still_url,
                "clip_url": s.clip_url,
                "prompt": s.prompt,
                "duration_seconds": s.duration_seconds,
            }
            for s in approved
        ],
    }
    local_path.with_suffix(".json").write_text(json.dumps(manifest, indent=2))

    # Determine whether we have real remote assets to download.
    # Mock adapters return file:// paths that don't exist; skip ffmpeg in that case.
    has_real_assets = any(
        (s.clip_url or s.still_url or "").startswith("https://")
        for s in approved
    )
    if not has_real_assets:
        cost = CostEntry(node="assemble", provider="local", amount_usd=0.0)
        return {"final_video_path": output_path, "cost_log": [cost]}

    with tempfile.TemporaryDirectory(prefix="pe_assemble_") as tmp_dir:
        tmp = Path(tmp_dir)
        segment_paths: list[Path] = []

        for i, shot in enumerate(approved):
            seg_path = tmp / f"seg_{i:03d}.mp4"
            if shot.mode == ShotMode.motion and shot.clip_url:
                raw = tmp / f"clip_{i:03d}.mp4"
                await _fetch(shot.clip_url, raw)
                # Re-encode to a common baseline so concat filter works.
                await asyncio.to_thread(_ffmpeg_reencode, raw, seg_path, shot.duration_seconds)
            else:
                still = tmp / f"still_{i:03d}.jpg"
                await _fetch(shot.still_url, still)
                await asyncio.to_thread(_ffmpeg_still_to_video, still, seg_path, shot.duration_seconds)
            segment_paths.append(seg_path)

        # Concatenate all segments.
        concat_path = tmp / "concat.mp4"
        await asyncio.to_thread(_ffmpeg_concat, segment_paths, concat_path)

        # Mix voiceover.
        if state.voiceover_url:
            audio_path = tmp / "voiceover.mp3"
            await _fetch(state.voiceover_url, audio_path)
            await asyncio.to_thread(_ffmpeg_mix_audio, concat_path, audio_path, local_path)
        else:
            import shutil
            shutil.copy2(concat_path, local_path)

    cost = CostEntry(node="assemble", provider="local", amount_usd=0.0)
    return {"final_video_path": output_path, "cost_log": [cost]}


# ── ffmpeg helpers (run in thread pool via asyncio.to_thread) ─────────────────


def _run(cmd: list[str]) -> None:
    import subprocess
    result = subprocess.run(cmd, capture_output=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"ffmpeg error: {result.stderr.decode(errors='replace')[-800:]}"
        )


def _ffmpeg_reencode(src: Path, dest: Path, duration: float) -> None:
    """Re-encode a video clip to a standard baseline for concat."""
    _run([
        "ffmpeg", "-y", "-i", str(src),
        "-t", str(duration),
        "-vf", "scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2",
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-an",  # audio stripped; voiceover is mixed in separately
        "-r", "24", str(dest),
    ])


def _ffmpeg_still_to_video(still: Path, dest: Path, duration: float) -> None:
    """Convert a still image to a video segment of the given duration."""
    _run([
        "ffmpeg", "-y",
        "-loop", "1", "-i", str(still),
        "-t", str(duration),
        "-vf", "scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2",
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-an",
        "-r", "24", str(dest),
    ])


def _ffmpeg_concat(segments: list[Path], dest: Path) -> None:
    """Concatenate segment files using the concat demuxer."""
    list_file = dest.parent / "segments.txt"
    list_file.write_text("\n".join(f"file '{p}'" for p in segments))
    _run([
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0", "-i", str(list_file),
        "-c", "copy", str(dest),
    ])


def _ffmpeg_mix_audio(video: Path, audio: Path, dest: Path) -> None:
    """Mix voiceover audio into the video, trimming audio to video duration."""
    _run([
        "ffmpeg", "-y",
        "-i", str(video), "-i", str(audio),
        "-map", "0:v:0", "-map", "1:a:0",
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest",  # trim audio to video length
        str(dest),
    ])
