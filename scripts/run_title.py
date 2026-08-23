"""Thin wrapper so `python scripts/run_title.py "What X Really Thought About Y"` works."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from channel.__main__ import main  # noqa: E402

if __name__ == "__main__":
    # Default to init when the first arg looks like a title.
    argv = sys.argv[1:]
    if argv and argv[0] not in {
        "init",
        "analyze",
        "research-seed",
        "chunks",
        "qa",
        "compile",
        "score-title",
        "suggest-titles",
        "originality",
        "youtube",
        "branding",
    }:
        argv = ["init", *argv]
    raise SystemExit(main(argv))
