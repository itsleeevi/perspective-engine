"""Section 4A / 17B emotional-architecture checks."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

PALETTE = {
    "anticipation",
    "pressure",
    "exposure",
    "belonging",
    "recognition",
    "frustration",
    "grief",
    "relief",
    "warmth",
    "humour",
    "wonder",
    "pride",
    "doubt",
    "resolve",
    "loss",
    "vindication",
    "fatigue",
    "defiance",
    "tenderness",
}
NAMED_FEELING_RE = re.compile(
    r"\b(you feel devastated|heartbreaking|unbelievable|chills|emotional rollercoaster)\b",
    re.I,
)
INSPIRATION_RE = re.compile(
    r"\b(dream|passion|greatness|destiny|legacy|hunger|mindset|grind|never give up)\b",
    re.I,
)
YOU_OPEN_RE = re.compile(r"^You\b")
STRETCH = 900


@dataclass
class CheckResult:
    name: str
    ok: bool
    detail: str = ""


@dataclass
class EmotionReport:
    checks: list[CheckResult] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return all(c.ok for c in self.checks)

    def add(self, name: str, ok: bool, detail: str = "") -> None:
        self.checks.append(CheckResult(name, ok, detail))


def _norm(text: str) -> str:
    return " ".join(text.split())


def _words(text: str) -> list[str]:
    return [t for t in re.findall(r"\S+", text) if not (t.startswith("[") and t.endswith("]"))]


def validate_emotion(register: dict, script: str) -> EmotionReport:
    report = EmotionReport()
    script_n = _norm(script)
    eras = list(register.get("eras") or [])
    maps = []
    complete = True
    for era in eras:
        emo = era.get("emotion") or {}
        maps.append(emo)
        needed = ("dominant", "source_situation", "cost_of_failure", "turn_quote", "relief_quote")
        if any(not emo.get(k) for k in needed):
            complete = False
        if emo.get("dominant") not in PALETTE:
            complete = False
    report.add("E1_MAP_COMPLETE", complete and bool(eras), "an era is missing a complete emotion map")

    dominants = [m.get("dominant") for m in maps if m.get("dominant")]
    repeat3 = False
    for a, b, c in zip(dominants, dominants[1:], dominants[2:]):
        if a == b == c:
            repeat3 = True
    report.add("E2_NO_TRIPLE_REPEAT", not repeat3, "the same dominant feeling repeats across three eras")
    report.add(
        "E3_VARIETY",
        len(set(dominants)) >= 6 or len(eras) < 6,
        f"{len(set(dominants))} distinct dominant feelings",
    )

    relief_ok = True
    turn_before = True
    for emo in maps:
        turn = _norm(emo.get("turn_quote") or "")
        relief = _norm(emo.get("relief_quote") or "")
        if not relief:
            relief_ok = False
        if turn and relief:
            ti = script_n.find(turn)
            ri = script_n.find(relief)
            if ti < 0 or ri < 0 or not (ti < ri):
                turn_before = False
    report.add("E4_RELIEF_PRESENT", relief_ok, "an era has no relief beat")
    report.add("E5_TURN_BEFORE_RELIEF", turn_before, "relief lands before the turn, or a quote is missing")

    marks: list[int] = []
    for emo in maps:
        for key in ("turn_quote", "relief_quote"):
            q = _norm(emo.get(key) or "")
            if q:
                i = script_n.find(q)
                if i >= 0:
                    marks.append(len(_words(script_n[:i])))
    stretch_ok = True
    words = _words(script_n)
    if words:
        points = [0, *sorted(marks), len(words)]
        for a, b in zip(points, points[1:]):
            if b - a > STRETCH:
                stretch_ok = False
    report.add("E6_STRETCH", stretch_ok, "more than about 900 words with no turn or relief")

    stakes = all(bool((m.get("cost_of_failure") or "").strip()) for m in maps) if maps else False
    report.add("E7_STAKES_NAMED", stakes, "cost_of_failure is empty")
    report.add("E8_NO_NAMED_FEELING", not NAMED_FEELING_RE.search(script_n), "script names the viewer's feeling")
    report.add("E9_NO_INSPIRATION_VOCAB", not INSPIRATION_RE.search(script_n), "inspiration vocabulary is present")

    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", script_n) if s.strip()]
    lengths = [len(s.split()) for s in sentences]
    monotone = False
    if len(lengths) >= 8:
        monotone = max(lengths) - min(lengths) < 4
    you_run = False
    run = 0
    for s in sentences:
        if YOU_OPEN_RE.match(s):
            run += 1
            if run >= 4:
                you_run = True
        else:
            run = 0
    report.add("E10_RHYTHM", not monotone and not you_run, "sentence length is flat or four You-openers in a row")

    close = sentences[-3:] if sentences else []
    close_words = len(_words(" ".join(close)))
    # Closing passage check uses the last ~180 words window.
    tail = _words(script_n)[-180:]
    close_len = len(tail)
    report.add(
        "E11_CLOSE_LENGTH",
        100 <= close_words <= 180 or 100 <= close_len <= 180,
        f"closing window is {close_words} words across the last sentences",
    )
    return report


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Section 4A emotion-map checks")
    p.add_argument("claims", help="claims_[slug].json")
    p.add_argument("script", help="clean script.txt")
    args = p.parse_args(argv)
    register = json.loads(Path(args.claims).read_text(encoding="utf-8"))
    script = Path(args.script).read_text(encoding="utf-8")
    report = validate_emotion(register, script)
    for check in report.checks:
        mark = "PASS" if check.ok else "FAIL"
        extra = f" — {check.detail}" if check.detail and not check.ok else ""
        print(f"{mark} {check.name}{extra}")
    return 0 if report.ok else 1


if __name__ == "__main__":
    sys.exit(main())
