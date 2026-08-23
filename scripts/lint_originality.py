"""
Originality linter — mass-production detector for channel cuts.

Compares a candidate fixture + storyboard against the last N shipped videos.
Blocks image generation and assembly when ORIGINALITY_SCORE < 80.

    .venv/bin/python scripts/lint_originality.py fixtures/video_specs/<slug>.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main() -> None:
    if len(sys.argv) < 2:
        print("usage: lint_originality.py <spec.json>", file=sys.stderr)
        sys.exit(2)
    spec_path = ROOT / sys.argv[1]
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    slug = Path(spec.get("fixture") or "").stem

    sys.path.insert(0, str(ROOT))
    from channel.originality import originality_report_for_slug, regenerate_targets
    from channel.originality_policy import ORIGINALITY_SCORE_MIN

    report = originality_report_for_slug(slug)
    print(f"slug: {slug}")
    print(f"originality_score: {report.originality_score} (min {ORIGINALITY_SCORE_MIN})")
    print(f"peak_recent_similarity: {report.mass_production_similarity}")

    if report.comparisons:
        worst = max(report.comparisons, key=lambda c: c.weighted())
        print(
            f"closest_recent: {worst.compared_slug} "
            f"(weighted {worst.weighted():.0f})"
        )
        print(
            "  hook={:.0f} phrasing={:.0f} structure={:.0f} scenes={:.0f} "
            "visual={:.0f} transitions={:.0f} conclusion={:.0f} thumb={:.0f}".format(
                worst.hook,
                worst.phrasing,
                worst.structure,
                worst.scene_sequence,
                worst.visual_composition,
                worst.transitions,
                worst.conclusion,
                worst.thumbnail,
            )
        )

    for flag in report.flags:
        print(f"flag    {flag}")

    if report.ready_for_images:
        print("\nOriginality passes.")
        sys.exit(0)

    targets = regenerate_targets(report)
    print("\nOriginality FAILED. Regenerate: " + ", ".join(targets or ["story"]))
    sys.exit(1)


if __name__ == "__main__":
    main()
