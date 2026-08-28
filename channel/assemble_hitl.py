"""Assemble a HITL job: pause-timed still holds + mux imported voice-over."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from channel.ingest import expected_image_names, match_images
from channel.job import ARTIFACTS, JobState, job_dir, load_manifest, write_manifest, write_operator_md, write_report
from channel.pauses import load_timestamps
from graph.nodes.assemble import (
    _cumulative_frame_counts,
    _ffmpeg_concat,
    _ffmpeg_mix_audio,
    _ffmpeg_still_to_video,
)

FPS = 30
WIDTH = 3840
HEIGHT = 2160


def assemble_hitl(
    job_id: str,
    *,
    artifacts_root: Path | None = None,
    burn_captions: bool | None = None,
) -> Path:
    from graph.captions import overlay_scene_caption
    from PIL import Image
    from scripts._media import cover_crop

    root = artifacts_root or ARTIFACTS
    job = job_dir(job_id, root=root)
    spec_files = sorted((job / "fixtures" / "video_specs").glob("*.json"))
    if not spec_files:
        raise FileNotFoundError(f"no video spec in {job / 'fixtures' / 'video_specs'}")
    spec = json.loads(spec_files[0].read_text(encoding="utf-8"))
    ts_path = job / "timestamps.json"
    if not ts_path.is_file():
        raise FileNotFoundError(f"no timestamps.json in {job}")
    table = load_timestamps(ts_path)
    rows = list(table.get("scenes") or [])
    if not rows:
        raise ValueError("timestamps.json has no scenes")
    audio = job / "audio" / "voiceover.wav"
    if not audio.is_file():
        raise FileNotFoundError(f"no imported voiceover at {audio}")
    expected = expected_image_names(table)
    stills = match_images(job / "images", expected)
    durations = [float(r["end"]) - float(r["start"]) for r in rows]
    frame_counts = _cumulative_frame_counts(durations, FPS)
    if burn_captions is None:
        drop_cut = str(spec.get("cut_source") or table.get("cut_source") or "") == (
            "drop_filename_timestamps"
        )
        burn = False if drop_cut else bool(spec.get("burn_captions", True))
    else:
        burn = bool(burn_captions)
    slug = Path(spec.get("fixture") or job_id).stem
    output = job / "final" / f"{slug}.mp4"
    output.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="pe_hitl_") as tmp_dir:
        tmp = Path(tmp_dir)
        segments = []
        for i, (row, src, frames) in enumerate(zip(rows, stills, frame_counts, strict=True)):
            fitted = src
            with Image.open(src) as im:
                already_4k = im.size == (WIDTH, HEIGHT)
            if not already_4k:
                fitted = tmp / f"still_{i:03d}.png"
                cover_crop(src, fitted, 16, 9, out_size=(WIDTH, HEIGHT))
            if burn:
                caption = str(row.get("text") or "").strip()
                if caption:
                    captioned = tmp / f"caption_{i:03d}.png"
                    overlay_scene_caption(fitted, captioned, caption)
                    fitted = captioned
            seg = tmp / f"seg_{i:03d}.mp4"
            _ffmpeg_still_to_video(fitted, seg, frames, WIDTH, HEIGHT, FPS)
            segments.append(seg)
        concat = tmp / "concat.mp4"
        _ffmpeg_concat(segments, concat)
        _ffmpeg_mix_audio(concat, audio, output)

    manifest = load_manifest(job_id, root=root)
    manifest.state = JobState.ready
    manifest.paths["video"] = str(output)
    manifest.notes = [f"Assembled {output}"]
    write_manifest(manifest, root=root)
    write_report(manifest, root=root)
    write_operator_md(manifest, root=root)
    return output
