"""
Render the YouTube Short companion of a long custom video.

    .venv/bin/python scripts/run_short.py fixtures/video_specs/<slug>.json

The Short exists to drive traffic to the long video: a vertical 1080x1920
cut of 25-45 seconds that opens on the story's most ironic image, escalates
two or three beats, and cuts off right BEFORE the payoff with a spoken
call-to-action. It must open a loop, not close one — never spoil the long
video's ending.

Reusable by data, like the long form. The video spec carries a "short" block:

    "short": {
      "fixture":       "fixtures/<slug>_short.json",
      "stills_module": "fixtures/<slug>_short_stills.py",
      "still_prefix":  "<slug>_short_",
      "stills_dir":    "assets/grok_<slug>_short",
      "output":        "assets/output/<slug>_short.mp4"
    }

The short fixture uses the normal fixture schema with
``include_level_titles: false`` (no chapter cards in 40 seconds). Stills are
generated at 9:16 from the jobs file written by
``make_image_jobs.py <spec> --short``; lint with
``lint_story.py <spec> --short`` and ``lint_storyboard.py <spec> --short``.

No LangGraph here: a Short needs voice + stills + ffmpeg, so this is a lean
assembler that reuses the long-form pipeline's pieces (Chatterbox adapter
with whisper-aligned durations, drift-free frame snapping, fill-frame
scaling) at portrait resolution.
"""

from __future__ import annotations

import asyncio
import importlib.util
import json
import os
import sys
import tempfile
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
load_dotenv(ROOT / ".env", override=True)
os.environ.setdefault("ADAPTER_CACHE", "1")

if len(sys.argv) < 2:
    print("usage: run_short.py <spec.json>", file=sys.stderr)
    sys.exit(2)
SPEC = json.loads((ROOT / sys.argv[1]).read_text(encoding="utf-8"))
if "short" not in SPEC:
    print("spec has no \"short\" block; nothing to render", file=sys.stderr)
    sys.exit(2)
SHORT = SPEC["short"]
from channel.pacing import apply_spec_pacing  # noqa: E402

apply_spec_pacing(SPEC)
if SPEC.get("voice_ref"):
    os.environ.setdefault("CHATTERBOX_VOICE_REF", str(ROOT / SPEC["voice_ref"]))
if SPEC.get("chatterbox_breath") is not None:
    os.environ.setdefault("CHATTERBOX_BREATH", str(SPEC["chatterbox_breath"]))
if SPEC.get("chatterbox_temperature") is not None:
    os.environ.setdefault("CHATTERBOX_TEMPERATURE", str(SPEC["chatterbox_temperature"]))
if SPEC.get("kokoro_voice"):
    os.environ["KOKORO_VOICE"] = str(SPEC["kokoro_voice"])
if SPEC.get("kokoro_speed") is not None:
    os.environ["KOKORO_SPEED"] = str(SPEC["kokoro_speed"])
if SPEC.get("kokoro_sentence_pause") is not None:
    os.environ["KOKORO_SENTENCE_PAUSE"] = str(SPEC["kokoro_sentence_pause"])
if SPEC.get("kokoro_clause_pause") is not None:
    os.environ["KOKORO_CLAUSE_PAUSE"] = str(SPEC["kokoro_clause_pause"])

from graph.nodes.assemble import (  # noqa: E402
    _cumulative_frame_counts,
    _ffmpeg_concat,
    _ffmpeg_mix_audio,
    _ffmpeg_still_to_video,
)
from graph.script_fixture import (  # noqa: E402
    fixture_to_beats,
    is_title_beat,
    load_fixture,
    split_beat_into_chunks,
)
from graph import style  # noqa: E402
from scripts._media import cover_crop  # noqa: E402

WIDTH, HEIGHT = 1080, 1920
CURSOR_ASSETS = Path.home() / ".cursor" / "projects" / (
    str(ROOT).strip("/").replace("/", "-")
) / "assets"


def _chunks() -> list[str]:
    data = load_fixture(str(ROOT / SHORT["fixture"]))
    beats = fixture_to_beats(data, include_hook=True)
    chunks: list[str] = []
    for beat in beats:
        if is_title_beat(beat):
            raise ValueError("Shorts have no chapter cards; remove [TITLE] beats.")
        chunks.extend(split_beat_into_chunks(beat))
    return chunks


def _stills_count() -> int:
    spec = importlib.util.spec_from_file_location(
        "short_stills", ROOT / SHORT["stills_module"]
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return len(module.STILLS)


def gather_stills(n: int) -> list[Path]:
    prefix = SHORT["still_prefix"]
    stills_dir = ROOT / SHORT["stills_dir"]
    stills_dir.mkdir(parents=True, exist_ok=True)
    missing: list[Path] = []
    for i in range(n):
        name = f"{prefix}{i:03d}.png"
        dest = stills_dir / name
        src = CURSOR_ASSETS / name
        if src.is_file() and src.stat().st_size > 0:
            cover_crop(src, dest, 9, 16)
            continue
        if not (dest.is_file() and dest.stat().st_size > 0):
            missing.append(dest)
    return missing


async def main() -> None:
    chunks = _chunks()
    n_stills = _stills_count()
    if len(chunks) != n_stills:
        print(
            f"short storyboard has {n_stills} scenes, script has {len(chunks)} "
            "chunks — run lint_storyboard.py --short",
            file=sys.stderr,
        )
        sys.exit(1)
    missing = gather_stills(n_stills)
    if missing:
        print(f"missing {len(missing)} stills, e.g. {missing[0].name}", file=sys.stderr)
        sys.exit(2)

    if SPEC.get("voice", "chatterbox") == "kokoro":
        from adapters.voice.kokoro import KokoroVoiceAdapter as Adapter
    else:
        from adapters.voice.chatterbox import ChatterboxVoiceAdapter as Adapter
    vo = await Adapter().synthesize(chunks, [3.0] * len(chunks))
    total = vo.duration_seconds
    if total > 60.0:
        print(f"short is {total:.1f}s — over the 60s Shorts sweet spot; cut beats",
              file=sys.stderr)
        sys.exit(1)
    if total > 45.0:
        print(f"warning: {total:.1f}s — 25-45s converts best for traffic Shorts")

    fps = style.FPS
    durations = vo.beat_durations
    frame_counts = _cumulative_frame_counts(durations, fps)

    out_path = ROOT / SHORT["output"]
    out_path.parent.mkdir(parents=True, exist_ok=True)
    stills_dir = ROOT / SHORT["stills_dir"]
    prefix = SHORT["still_prefix"]

    with tempfile.TemporaryDirectory(prefix="pe_short_") as tmp_dir:
        tmp = Path(tmp_dir)
        segments: list[Path] = []
        for i, frames in enumerate(frame_counts):
            seg = tmp / f"seg_{i:03d}.mp4"
            _ffmpeg_still_to_video(
                stills_dir / f"{prefix}{i:03d}.png", seg, frames, WIDTH, HEIGHT, fps
            )
            segments.append(seg)
        concat = tmp / "concat.mp4"
        _ffmpeg_concat(segments, concat)
        audio = Path(vo.audio_url.removeprefix("file://"))
        _ffmpeg_mix_audio(concat, audio, out_path)

    cut_error = []
    elapsed_frames, elapsed = 0, 0.0
    for frames, dur in zip(frame_counts, durations):
        cut_error.append(abs(elapsed_frames / fps - elapsed) * 1000)
        elapsed_frames += frames
        elapsed += dur
    manifest = {
        "kind": "short",
        "parent_topic": SPEC["topic"],
        "resolution": f"{WIDTH}x{HEIGHT}",
        "fps": fps,
        "shots": len(chunks),
        "duration_seconds": round(total, 2),
        "voiceover_url": vo.audio_url,
        "sync": {
            "max_cut_error_ms": round(max(cut_error), 2) if cut_error else 0.0,
            "half_frame_ms": round(500.0 / fps, 2),
        },
        "chunks": chunks,
    }
    out_path.with_suffix(".json").write_text(json.dumps(manifest, indent=2))
    print(f"short: {out_path} ({total:.1f}s, {len(chunks)} shots, "
          f"max cut error {manifest['sync']['max_cut_error_ms']}ms)")


if __name__ == "__main__":
    asyncio.run(main())
