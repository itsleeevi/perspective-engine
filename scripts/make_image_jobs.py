"""
Write the image-jobs JSON for a video spec — one job per narration chunk.

    .venv/bin/python scripts/make_image_jobs.py fixtures/video_specs/<slug>.json
    .venv/bin/python scripts/make_image_jobs.py fixtures/video_specs/<slug>.json --short

Output: fixtures/<still_prefix>image_jobs.json, consumed by the stills
generation subagents (they call GenerateImage with each job's ``prompt`` and
``filename`` at the job's ``aspect``: 16:9 for the long video, 9:16 for the
Short companion). Run scripts/lint_storyboard.py first; this script refuses
to write jobs for a storyboard whose scene count does not match the
narration chunks.
"""

from __future__ import annotations

import importlib.util
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main() -> None:
    if len(sys.argv) < 2:
        print("usage: make_image_jobs.py <spec.json>", file=sys.stderr)
        sys.exit(2)
    spec = json.loads((ROOT / sys.argv[1]).read_text(encoding="utf-8"))
    short = "--short" in sys.argv[2:]
    aspect = "9:16" if short else "16:9"
    if short:
        if "short" not in spec:
            print("spec has no \"short\" block", file=sys.stderr)
            sys.exit(2)
        spec = {**spec, **spec["short"]}
    sys.path.insert(0, str(ROOT))
    from channel.pacing import apply_spec_pacing

    apply_spec_pacing(spec)
    from graph.script_fixture import (
        fixture_to_beats,
        is_title_beat,
        load_fixture,
        split_beat_into_chunks,
    )

    mspec = importlib.util.spec_from_file_location(
        "stills", ROOT / spec["stills_module"]
    )
    module = importlib.util.module_from_spec(mspec)
    assert mspec.loader is not None
    mspec.loader.exec_module(module)

    stills = list(module.STILLS)
    data = load_fixture(str(ROOT / spec["fixture"]))
    chunks = [
        c
        for beat in fixture_to_beats(data, include_hook=True)
        if not is_title_beat(beat)
        for c in split_beat_into_chunks(beat)
    ]
    if len(chunks) != len(stills):
        print(
            f"scene count {len(stills)} != chunk count {len(chunks)}; "
            "run lint_storyboard.py",
            file=sys.stderr,
        )
        sys.exit(1)

    prefix = spec["still_prefix"]
    jobs = []
    for i, ((shot_type, who, scene), chunk) in enumerate(zip(stills, chunks)):
        jobs.append(
            {
                "id": f"{i:03d}",
                "filename": f"{prefix}{i:03d}.png",
                "aspect": aspect,
                "who": who,
                "free": who == "empty",
                "shot_type": shot_type,
                "chunk": chunk,
                "scene": scene,
                "prompt": module.prompt_for(who, scene),
            }
        )
    out = ROOT / "fixtures" / f"{prefix}image_jobs.json"
    out.write_text(json.dumps({"jobs": jobs}, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {out} ({len(jobs)} jobs)")


if __name__ == "__main__":
    main()
