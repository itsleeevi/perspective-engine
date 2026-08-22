"""
assemble node — compose stills, title cards, and narration into a 4K MP4.

Each shot becomes one video segment, segments are concatenated in shot order,
and the narration is muxed in.

Three things here are what make the output watchable rather than a slideshow:

*Resolution.* Stills are generated at 1280x720 and upscaled to 3840x2160 with
lanczos. Flat vector art survives this cleanly — there is no fine texture to
smear — and a 4K upload also gets YouTube's higher bitrate allocation, which
matters most for large flat colour areas.

*No motion.* Every shot is a perfectly steady hold, no Ken Burns pan/zoom.
The reference format cuts on the picture, not on camera movement, and with
shots now averaging 2-3 seconds any zoom would be too subtle to register
before the next cut anyway — it would only cost render time.

*No black bars.* Stills are scaled with ``force_original_aspect_ratio=increase``
and then cropped to the output frame, so a 3:2 Grok still still fills 16:9
instead of sitting in pillarbox.

*No truncation.* Segment durations come from the measured length of each
narration beat; the audio is then padded rather than cut. The old
``-shortest`` mux silently clipped the end of the narration.

*No drift.* Naively rounding every shot's own duration up to a whole frame
looks harmless per shot, but the remainder only ever accumulates in one
direction across a concatenated video: with shots now averaging 2-3 seconds,
a 15-25 minute video is 300-600 shots, and independent per-shot rounding can
drift the picture multiple seconds behind the narration by the end. Frame
counts are instead derived from cumulative frame-boundary snapping (see
``_cumulative_frame_counts``), which keeps every cut within half a frame of
the true narration timeline regardless of shot count.
"""

from __future__ import annotations

import asyncio
import json
import math
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

import httpx

from graph import style
from graph.assets import local_asset_url
from graph.captions import overlay_scene_caption
from graph.script_fixture import is_title_beat, title_card_lines
from graph.state import CostEntry, PipelineState, Shot, ShotMode, ShotStatus

_FETCH_TIMEOUT = 60.0

# Concurrent ffmpeg segment encodes. 4K encoding is CPU-bound; a few in
# parallel saturates the machine without thrashing it.
_ENCODE_CONCURRENCY = 3


def _slug(topic: str) -> str:
    safe = re.sub(r"[^a-z0-9]+", "_", topic.lower()).strip("_")
    return safe[:40]


async def _fetch(url: str, dest: Path) -> None:
    """Download a URL (https:// or file://) to dest."""
    if url.startswith("file://"):
        shutil.copy2(url.removeprefix("file://"), dest)
        return
    async with httpx.AsyncClient(timeout=_FETCH_TIMEOUT, follow_redirects=True) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        dest.write_bytes(resp.content)


def _asset_exists(url: str) -> bool:
    """True if the URL points at a remote asset or a file that is really there."""
    if not url:
        return False
    if url.startswith("file://"):
        return Path(url.removeprefix("file://")).is_file()
    return url.startswith("https://")


def _cumulative_frame_counts(durations: list[float], fps: int) -> list[int]:
    """
    Convert per-shot durations into exact frame counts without accumulating
    rounding drift.

    Independently rounding each shot's own duration up to a whole frame
    (``ceil(duration * fps)``) leaves up to one frame of remainder on every
    single shot, and concatenated segments only ever add those remainders in
    the same direction — by shot 500 of a long video the picture can be
    seconds behind where the narration actually is. Snapping each shot's
    *cumulative* end time to the frame grid instead means every individual
    cut is off by at most half a frame from the true narration timeline, no
    matter how many shots precede it — the error never compounds.

    The very last boundary rounds up rather than to nearest, so the
    concatenated video's total length is never shorter than the audio track
    it gets muxed with (``_ffmpeg_mix_audio`` pads audio to match, and can
    only do that safely if video >= audio).
    """
    if not durations:
        return []
    counts: list[int] = []
    prev_frame = 0
    cumulative_seconds = 0.0
    last_index = len(durations) - 1
    for i, duration in enumerate(durations):
        cumulative_seconds += duration
        target = cumulative_seconds * fps
        frame = math.ceil(target - 1e-6) if i == last_index else round(target)
        frame = max(frame, prev_frame + 1)  # every shot renders at least one frame
        counts.append(frame - prev_frame)
        prev_frame = frame
    return counts


def _chapters(shots: list[Shot]) -> list[dict]:
    """Start time of each level, for YouTube chapter markers."""
    chapters: list[dict] = []
    elapsed = 0.0
    for shot in shots:
        if shot.is_title_card or is_title_beat(shot.prompt):
            line1, line2 = title_card_lines(shot.prompt)
            label = f"{line1.rstrip(':')}: {line2}".strip().rstrip(":")
            chapters.append({"start_seconds": round(elapsed, 2), "label": label})
        elapsed += shot.duration_seconds
    return chapters


async def assemble(state: PipelineState) -> dict:
    """
    Download all assets and compose the final MP4 via ffmpeg.

    Returns a partial state update: ``final_video_path``, ``cost_log``.
    """
    approved = [
        s
        for s in state.shot_list
        if s.status in (ShotStatus.approved, ShotStatus.escalated)
    ]

    height = state.output_height or style.OUTPUT_HEIGHT
    width = height * 16 // 9
    fps = style.FPS

    slug = _slug(state.topic)
    output_path = local_asset_url(f"output/{slug}_final.mp4")
    local_path = Path(output_path.removeprefix("file://"))
    local_path.parent.mkdir(parents=True, exist_ok=True)

    chapters = _chapters(approved)
    motion_count = sum(1 for s in approved if s.mode == ShotMode.motion)

    # Frame counts are what actually gets rendered; the per-shot durations are
    # only the request. Computing them before the manifest is written lets the
    # manifest report where each cut truly lands, so a claim about audio/video
    # sync can be checked against the file instead of taken on trust.
    frame_counts = _cumulative_frame_counts(
        [s.duration_seconds for s in approved], fps
    )
    cut_seconds: list[float] = []
    elapsed_frames = 0
    for count in frame_counts:
        cut_seconds.append(elapsed_frames / fps)
        elapsed_frames += count
    intended_seconds: list[float] = []
    elapsed = 0.0
    for shot in approved:
        intended_seconds.append(elapsed)
        elapsed += shot.duration_seconds
    cut_error_ms = [
        abs(actual - intended) * 1000.0
        for actual, intended in zip(cut_seconds, intended_seconds, strict=True)
    ]

    manifest = {
        "topic": state.topic,
        "resolution": f"{width}x{height}",
        "fps": fps,
        "total_shots": len(approved),
        "motion_shots": motion_count,
        "static_shots": len(approved) - motion_count,
        "title_cards": sum(1 for s in approved if s.is_title_card),
        "estimated_duration_seconds": round(
            sum(s.duration_seconds for s in approved), 2
        ),
        "voiceover_url": state.voiceover_url,
        # Every cut's distance from the narration timeline it was measured
        # against. Bounded by half a frame (~16.7ms at 30fps) by construction,
        # and reported so that "the picture is in sync with the voice" is an
        # inspectable number rather than an assurance.
        "sync": {
            "max_cut_error_ms": round(max(cut_error_ms), 2) if cut_error_ms else 0.0,
            "half_frame_ms": round(500.0 / fps, 2),
        },
        "chapters": chapters,
        "burn_captions": state.burn_captions,
        "shots": [
            {
                "id": s.id,
                "start_seconds": round(start, 3),
                "mode": s.mode.value if hasattr(s.mode, "value") else str(s.mode),
                "status": s.status.value if hasattr(s.status, "value") else str(s.status),
                "is_title_card": s.is_title_card,
                "still_url": s.still_url,
                "clip_url": s.clip_url,
                "prompt": s.prompt,
                "narration": s.narration,
                "duration_seconds": s.duration_seconds,
            }
            for s, start in zip(approved, cut_seconds, strict=True)
        ],
    }
    local_path.with_suffix(".json").write_text(json.dumps(manifest, indent=2))

    # Title cards are always real files, so only generated shots tell us
    # whether this run has usable frames.
    generated = [s for s in approved if not s.is_title_card]
    missing = [
        s
        for s in generated
        if not (_asset_exists(s.clip_url) or _asset_exists(s.still_url))
    ]
    if generated and len(missing) == len(generated):
        # Mock adapters return file:// URLs for files they never wrote. There
        # is nothing for ffmpeg to do, but the run still exercised the full
        # graph and produced a manifest.
        cost = CostEntry(node="assemble", provider="local", amount_usd=0.0)
        return {"final_video_path": output_path, "cost_log": [cost]}
    if missing:
        raise RuntimeError(
            f"{len(missing)} of {len(generated)} shots have no asset on disk "
            f"(first: {missing[0].id}). Refusing to assemble a video with gaps."
        )

    with tempfile.TemporaryDirectory(prefix="pe_assemble_") as tmp_dir:
        tmp = Path(tmp_dir)
        segment_paths = [tmp / f"seg_{i:03d}.mp4" for i in range(len(approved))]
        semaphore = asyncio.Semaphore(_ENCODE_CONCURRENCY)

        async def build_segment(i: int, shot: Shot) -> None:
            seg_path = segment_paths[i]
            frames = frame_counts[i]
            if shot.mode == ShotMode.motion and shot.clip_url:
                raw = tmp / f"clip_{i:03d}.mp4"
                await _fetch(shot.clip_url, raw)
                async with semaphore:
                    await asyncio.to_thread(
                        _ffmpeg_reencode, raw, seg_path, frames, width, height, fps,
                    )
                return
            still = tmp / f"still_{i:03d}.png"
            await _fetch(shot.still_url, still)
            caption = (shot.narration or "").strip()
            if state.burn_captions and caption and not shot.is_title_card:
                captioned = tmp / f"caption_{i:03d}.png"
                await asyncio.to_thread(
                    overlay_scene_caption, still, captioned, caption
                )
                still = captioned
            async with semaphore:
                await asyncio.to_thread(
                    _ffmpeg_still_to_video, still, seg_path, frames, width, height, fps,
                )

        await asyncio.gather(
            *(build_segment(i, shot) for i, shot in enumerate(approved))
        )

        concat_path = tmp / "concat.mp4"
        await asyncio.to_thread(_ffmpeg_concat, segment_paths, concat_path)

        if state.voiceover_url:
            audio_path = tmp / "voiceover.mp3"
            await _fetch(state.voiceover_url, audio_path)
            await asyncio.to_thread(
                _ffmpeg_mix_audio, concat_path, audio_path, local_path
            )
        else:
            shutil.copy2(concat_path, local_path)

    cost = CostEntry(node="assemble", provider="local", amount_usd=0.0)
    return {"final_video_path": output_path, "cost_log": [cost]}


# ── ffmpeg helpers (run in thread pool via asyncio.to_thread) ─────────────────


def _run(cmd: list[str]) -> None:
    result = subprocess.run(cmd, capture_output=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"ffmpeg error: {result.stderr.decode(errors='replace')[-800:]}"
        )


def _fit(width: int, height: int) -> str:
    """Scale to FILL the frame. Crop overflow from the bottom, never the top.

    On-image labels live in the top band of channel stills. Centered crop
    shears them; y=0 keeps every badge inside the 4K frame.
    """
    return (
        f"scale={width}:{height}:flags=lanczos:force_original_aspect_ratio=increase,"
        f"crop={width}:{height}:(iw-{width})/2:0"
    )


def _x264(dest: Path, still: bool = False) -> list[str]:
    """Common encoder settings. CRF 20 keeps flat colour fields banding-free."""
    args = [
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "20",
        "-pix_fmt", "yuv420p",
        "-profile:v", "high",
        # Short GOP so every hard cut lands on a keyframe.
        "-g", "60",
        "-an",
    ]
    if still:
        args += ["-tune", "stillimage"]
    return args + [str(dest)]


def _ffmpeg_still_to_video(
    still: Path,
    dest: Path,
    frames: int,
    width: int,
    height: int,
    fps: int,
) -> None:
    """Render a still as a perfectly steady (no pan/zoom) video segment."""
    vf = f"{_fit(width, height)},fps={fps}"

    _run([
        "ffmpeg", "-y", "-loglevel", "error",
        "-loop", "1", "-framerate", str(fps), "-i", str(still),
        "-frames:v", str(frames),
        "-vf", vf,
        *_x264(dest, still=True),
    ])


def _ffmpeg_reencode(
    src: Path, dest: Path, frames: int, width: int, height: int, fps: int
) -> None:
    """Re-encode a motion clip to the common segment baseline."""
    _run([
        "ffmpeg", "-y", "-loglevel", "error", "-i", str(src),
        "-frames:v", str(frames),
        "-vf", f"{_fit(width, height)},fps={fps}",
        *_x264(dest),
    ])


def _ffmpeg_concat(segments: list[Path], dest: Path) -> None:
    """Concatenate segments without re-encoding (identical encode settings)."""
    list_file = dest.parent / "segments.txt"
    list_file.write_text("\n".join(f"file '{p}'" for p in segments))
    _run([
        "ffmpeg", "-y", "-loglevel", "error",
        "-f", "concat", "-safe", "0", "-i", str(list_file),
        "-c", "copy", "-movflags", "+faststart", str(dest),
    ])


def _ffmpeg_mix_audio(video: Path, audio: Path, dest: Path) -> None:
    """
    Mux narration into the video.

    ``apad`` + ``-shortest`` pads the audio with silence to the video length;
    because segment durations are rounded up from the measured narration, the
    video is always the longer of the two and no narration is ever cut.
    """
    _run([
        "ffmpeg", "-y", "-loglevel", "error",
        "-i", str(video), "-i", str(audio),
        "-map", "0:v:0", "-map", "1:a:0",
        "-af", "apad",
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
        "-shortest",
        "-movflags", "+faststart",
        str(dest),
    ])
