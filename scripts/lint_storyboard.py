"""
Storyboard linter — catches the failures that made past cuts feel generic,
BEFORE any image is generated.

    .venv/bin/python scripts/lint_storyboard.py fixtures/video_specs/<slug>.json

Checks (all measured on the stills module's ``STILLS`` scenes):

1. COUNT     — scene count must equal narration chunk count at the spec's WPM.
2. PROPS     — a signature prop must not appear in most of the film.
               The v4 Hitler cut put THE BOOK in 40+ of 77 frames; a movie
               shows the gun in act one, twice in the middle, and in the last
               shot — not in every scene. Budgets come from the module's
               ``PROP_BUDGET`` dict (prop token -> max scenes), defaulting
               to 6 for any ALL-CAPS "THE X" token found in scenes.
3. SETS      — no more than 3 consecutive scenes in the same locked set,
               and no set in more than a third of all scenes.
4. FLATLAYS  — object-on-table shots ("top-down flatlay", "symbolic graphic")
               capped at 25%: they read as slides, not cinema.
5. HERO REST — the hero should disappear for stretches (other characters and
               places carry scenes); flag if hero appears in >45% of scenes.
               Person-titled cuts also warn below 28%.
6. QUALITY BAR — unique cinema beats; ban filing-table wallpaper; signature
               prop must be huge / high contrast / large in frame
               (docs/video-engine/QUALITY_BAR.md).

Exit code 1 on any ERROR; warnings print but pass. A cheap execution model
runs this after writing the storyboard and fixes what it flags.
"""

from __future__ import annotations

import importlib.util
import json
import os
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _fail(msg: str) -> None:
    print(f"ERROR   {msg}")
    _fail.count += 1  # type: ignore[attr-defined]


_fail.count = 0  # type: ignore[attr-defined]


def _warn(msg: str) -> None:
    print(f"warning {msg}")


def main() -> None:
    if len(sys.argv) < 2:
        print("usage: lint_storyboard.py <spec.json> [--short]", file=sys.stderr)
        sys.exit(2)
    spec = json.loads((ROOT / sys.argv[1]).read_text(encoding="utf-8"))
    short = "--short" in sys.argv[2:]
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
    stills: list[tuple[str, str, str]] = list(module.STILLS)
    scenes = [s[2] for s in stills]
    shot_types = [s[0] for s in stills]
    whos = [s[1] for s in stills]

    # 1. COUNT
    data = load_fixture(str(ROOT / spec["fixture"]))
    chunks = [
        c
        for beat in fixture_to_beats(data, include_hook=True)
        if not is_title_beat(beat)
        for c in split_beat_into_chunks(beat)
    ]
    if len(chunks) != len(scenes):
        _fail(
            f"scene count {len(scenes)} != narration chunk count {len(chunks)} "
            f"at NARRATION_WPM={os.environ['NARRATION_WPM']}"
        )
    else:
        print(f"ok      {len(scenes)} scenes == {len(chunks)} chunks")

    # 2. PROPS
    budget: dict[str, int] = dict(getattr(module, "PROP_BUDGET", {}))
    if not budget:
        found = Counter(
            tok for scene in scenes for tok in re.findall(r"THE [A-Z]+", scene)
        )
        budget = {tok: 6 for tok in found}
    for prop, cap in budget.items():
        n = sum(1 for scene in scenes if prop in scene)
        if n > cap:
            _fail(
                f"prop economy: {prop!r} appears in {n}/{len(scenes)} scenes "
                f"(budget {cap}). A signature prop is setup / turns / payoff, "
                "not wallpaper."
            )
        else:
            print(f"ok      {prop!r} in {n}/{len(scenes)} scenes (budget {cap})")

    # 3. SETS — declared sets only; a prop token is not a location.
    set_tokens = set(getattr(module, "SET_TOKENS", []))
    if not set_tokens and not getattr(module, "PROP_BUDGET", None):
        set_tokens = {
            tok for scene in scenes for tok in re.findall(r"THE [A-Z]+", scene)
        }
    for tok in sorted(set_tokens):
        total = sum(1 for s in scenes if tok in s)
        if not short and total > len(scenes) // 3:
            _fail(f"set variety: {tok!r} hosts {total}/{len(scenes)} scenes (max 1/3)")
        streak = best = 0
        for s in scenes:
            streak = streak + 1 if tok in s else 0
            best = max(best, streak)
        if best > 3:
            _fail(f"set variety: {best} consecutive scenes in {tok!r} (max 3)")

    # 4. FLATLAYS
    flat = sum(1 for t in shot_types if t in ("top-down flatlay", "symbolic graphic"))
    if flat > len(stills) * 0.25:
        _fail(
            f"cinema check: {flat}/{len(stills)} shots are flatlays/graphics "
            "(max 25%) — objects on tables read as slides, not scenes"
        )
    else:
        print(f"ok      {flat}/{len(stills)} flatlay/graphic shots")

    # 5. HERO REST — long form only; a 10-shot Short may ride the hero.
    hero_n = sum(1 for w in whos if w == "hero")
    if not short and hero_n > len(stills) * 0.45:
        _warn(
            f"hero in {hero_n}/{len(stills)} scenes — let other people and "
            "places carry stretches of the film"
        )
    else:
        print(f"ok      hero in {hero_n}/{len(stills)} scenes")

    # 5b. QUALITY BAR — unique cinema beats, oversized props, person-title hero floor.
    from channel.quality_bar import stills_quality_notes

    q_errors, q_warnings = stills_quality_notes(
        scenes,
        whos,
        title=str(
            spec.get("title")
            or spec.get("topic")
            or (spec.get("youtube") or {}).get("title")
            or ""
        ),
        prop_tokens=list(budget),
        short=short,
    )
    for msg in q_errors:
        _fail(msg)
    for msg in q_warnings:
        _warn(msg)

    # 6. SHORT LENGTH — a traffic Short is 8-14 shots.
    if short and not 6 <= len(stills) <= 14:
        _fail(f"short has {len(stills)} shots — aim for 8-12 (25-45 seconds)")

    if _fail.count:  # type: ignore[attr-defined]
        print(f"\n{_fail.count} error(s). Fix the storyboard before generating images.")
        sys.exit(1)
    print("\nStoryboard passes.")


if __name__ == "__main__":
    main()
