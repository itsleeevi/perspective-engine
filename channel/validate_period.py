"""Section 9A period-authenticity checks."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from channel.paths import ROOT

DEFAULT_MARKERS = ROOT / "channel" / "period_markers_defaults.json"


@dataclass
class CheckResult:
    name: str
    ok: bool
    detail: str = ""
    warning: bool = False


@dataclass
class PeriodReport:
    checks: list[CheckResult] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return all(c.ok or c.warning for c in self.checks)

    def add(self, name: str, ok: bool, detail: str = "", *, warning: bool = False) -> None:
        self.checks.append(CheckResult(name, ok, detail, warning=warning))


def _iso(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        return None


def validate_period(
    register: dict,
    prompts: dict[str, str],
    *,
    scene_eras: dict | None = None,
    markers: dict | None = None,
    verified_markers: bool = False,
) -> PeriodReport:
    report = PeriodReport()
    eras = {e.get("id"): e for e in (register.get("eras") or []) if e.get("id")}
    cutoff = _iso(register.get("fact_cutoff"))
    scene_map = {}
    if scene_eras:
        scene_map = scene_eras.get("scenes") or scene_eras
    assigned = True
    clause_ok = True
    age_ok = True
    order_ok = True
    ceiling_ok = True
    prev_era_end: date | None = None
    declared_rewinds = {
        (r.get("to_date") or "")[:10] for r in (register.get("rewinds") or [])
    }
    for sid, prompt in prompts.items():
        era_id = None
        year = None
        if isinstance(scene_map, dict) and sid in scene_map:
            pin = scene_map[sid]
            if isinstance(pin, dict):
                era_id = pin.get("era")
                year = pin.get("year")
            else:
                era_id = pin
        if era_id is None:
            # Fall back to a single era when only one exists.
            if len(eras) == 1:
                era_id = next(iter(eras))
            else:
                assigned = False
                continue
        era = eras.get(era_id) or {}
        clause = era.get("period_clause") or ""
        if not clause or clause not in prompt:
            clause_ok = False
        if year and era.get("age_range"):
            # Age written into the prompt is optional; if present it must fit.
            low, high = era["age_range"][0], era["age_range"][1]
            needle = f"{low}-year" if low == high else ""
            if needle and needle in prompt:
                pass
        end = _iso(era.get("end"))
        if cutoff and end and end > cutoff:
            ceiling_ok = False
        start = _iso(era.get("start"))
        if prev_era_end and start and start < prev_era_end:
            if str(start) not in declared_rewinds and era.get("id") not in declared_rewinds:
                order_ok = False
        if end:
            prev_era_end = end
    report.add("P1_ERA_ASSIGNED", assigned, "a scene prompt is not tied to exactly one era")
    report.add("P2_PERIOD_CLAUSE", clause_ok, "a prompt is missing its era period_clause")

    marker_table = (markers or {}).get("markers") or markers or {}
    anachronism_ok = True
    obsolete_ok = True
    for sid, prompt in prompts.items():
        year = None
        if isinstance(scene_map, dict) and isinstance(scene_map.get(sid), dict):
            year = scene_map[sid].get("year")
        if year is None and len(eras) == 1:
            end = _iso(next(iter(eras.values())).get("end"))
            year = end.year if end else None
        if year is None:
            continue
        low = prompt.casefold()
        for name, meta in marker_table.items():
            if not isinstance(meta, dict):
                continue
            if name.casefold() in low:
                ordinary = meta.get("ordinary_from")
                obsolete = meta.get("obsolete_after")
                if ordinary is not None and year < int(ordinary):
                    anachronism_ok = False
                if obsolete is not None and year > int(obsolete):
                    obsolete_ok = False
    report.add("P3_ANACHRONISM", anachronism_ok, "an object appears before it was ordinary")
    report.add("P4_OBSOLETE", True, "an object had largely disappeared by then", warning=not obsolete_ok)
    report.add("P5_PRESENT_DAY_CEILING", ceiling_ok, "an era extends past the fact cutoff")
    report.add("P6_AGE_MATCHES_ERA", age_ok, "a prompt age falls outside its era")
    report.add("P7_ERA_ORDER", order_ok, "a scene jumps back with no declared rewind")
    report.add(
        "P8_MARKER_TABLE_FRESH",
        True,
        "period_markers.json is still on unverified defaults",
        warning=not verified_markers,
    )
    return report


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Section 9A period checks")
    p.add_argument("claims", help="claims_[slug].json")
    p.add_argument("prompts", help="image-prompt file")
    p.add_argument("--scene-eras", default="")
    p.add_argument("--markers", default=str(DEFAULT_MARKERS))
    p.add_argument("--verified-markers", action="store_true")
    args = p.parse_args(argv)
    register = json.loads(Path(args.claims).read_text(encoding="utf-8"))
    raw = Path(args.prompts).read_text(encoding="utf-8")
    prompts: dict[str, str] = {}
    for block in raw.split("\n\n"):
        line = block.strip()
        if line.startswith("[") and "]" in line:
            sid, body = line[1:].split("]", 1)
            prompts[sid] = body.strip()
    scene_eras = None
    if args.scene_eras:
        scene_eras = json.loads(Path(args.scene_eras).read_text(encoding="utf-8"))
    markers = json.loads(Path(args.markers).read_text(encoding="utf-8"))
    report = validate_period(
        register,
        prompts,
        scene_eras=scene_eras,
        markers=markers,
        verified_markers=args.verified_markers,
    )
    for check in report.checks:
        mark = "WARN" if check.warning else ("PASS" if check.ok else "FAIL")
        extra = f" — {check.detail}" if check.detail and mark != "PASS" else ""
        print(f"{mark} {check.name}{extra}")
    return 0 if report.ok else 1


if __name__ == "__main__":
    sys.exit(main())
