"""Push a video spec's pacing into the environment.

Chunk sizing in ``graph.script_fixture.split_beat_into_chunks`` reads these
at call time. Always assign (do not setdefault) so a previous channel run
cannot leak 3–7s windows into an older spec that expects 2.5–5.5s.
"""

from __future__ import annotations

import os
from typing import Any


def apply_spec_pacing(spec: dict[str, Any]) -> None:
    os.environ["NARRATION_WPM"] = str(spec.get("narration_wpm", 175))
    os.environ["CHUNK_MIN_SECONDS"] = str(spec.get("chunk_min_seconds", 2.5))
    os.environ["CHUNK_MAX_SECONDS"] = str(spec.get("chunk_max_seconds", 5.5))
    os.environ["CHUNK_TARGET_SECONDS"] = str(spec.get("chunk_target_seconds", 4.0))
