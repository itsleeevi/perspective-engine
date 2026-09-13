"""Section 17B story and claims-register checks."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

QUANTITY_RE = re.compile(
    r"\b(?:\d{4}|age\s+\d+|\d+\s*%|\$\d|\d+\s+(?:million|billion|thousand|goals|wins|years))\b",
    re.I,
)
MIND_RE = re.compile(
    r"\b(secretly|truly believes|hates|dreams of|knows that)\b",
    re.I,
)
INVENTION_RE = re.compile(
    r"\b(near bankruptcy|last chance|betrayal|rock bottom|nobody believed)\b",
    re.I,
)
HEDGE_RE = re.compile(
    r"\b(later describe|sources disagree|alleged|reported|uncertain|contested)\b",
    re.I,
)
YEAR_RE = re.compile(r"\b(19|20)\d{2}\b")


@dataclass
class CheckResult:
    name: str
    ok: bool
    detail: str = ""
    warning: bool = False


@dataclass
class StoryReport:
    checks: list[CheckResult] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return all(c.ok or c.warning for c in self.checks)

    def add(self, name: str, ok: bool, detail: str = "", *, warning: bool = False) -> None:
        self.checks.append(CheckResult(name, ok, detail, warning=warning))


def _parse_iso(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        return None


def _age_on(birth: date, event: date) -> int:
    years = event.year - birth.year
    if (event.month, event.day) < (birth.month, birth.day):
        years -= 1
    return years


def _script_norm(text: str) -> str:
    return " ".join(text.split())


def validate_story(register: dict, script: str) -> StoryReport:
    report = StoryReport()
    script_n = _script_norm(script)
    claims = list(register.get("claims") or [])
    eras = list(register.get("eras") or [])
    rewinds = list(register.get("rewinds") or [])
    birth = _parse_iso(register.get("birth_date"))
    cutoff = _parse_iso(register.get("fact_cutoff"))
    ids = [c.get("id") for c in claims]

    schema_ok = True
    for claim in claims:
        needed = ["id", "text", "type", "sources", "certainty", "script_refs"]
        if any(not claim.get(k) and claim.get(k) != [] for k in ("id", "text", "type")):
            schema_ok = False
        if claim.get("type") == "quantity" and (not claim.get("unit") or not claim.get("scope")):
            schema_ok = False
        if claim.get("type") == "interpretation" and not claim.get("basis"):
            schema_ok = False
        for key in needed:
            if key not in claim:
                schema_ok = False
    report.add("S1_SCHEMA", schema_ok, "a claim is missing required fields for its type")
    report.add("S2_ID_UNIQUE", len(ids) == len(set(ids)), "duplicate claim id")

    sourced = True
    quote_ok = True
    quality_ok = True
    for claim in claims:
        if claim.get("type") not in {"event", "quantity", "quotation", "role"}:
            continue
        sources = claim.get("sources") or []
        if not any(s.get("url") and s.get("supporting_text") for s in sources):
            sourced = False
        if claim.get("type") == "quotation":
            quoted = _script_norm(claim.get("text") or "")
            if not any(quoted and quoted in _script_norm(s.get("supporting_text") or "") for s in sources):
                quote_ok = False
        if claim.get("certainty") == "verified" and claim.get("type") == "event":
            if not any(s.get("kind") in {"primary", "independent"} for s in sources):
                quality_ok = False
    report.add("S3_SOURCED", sourced, "event/quantity/quotation/role claim lacks url + supporting_text")
    report.add("S4_QUOTE_VERBATIM", quote_ok, "quotation is not inside supporting_text")
    report.add("S5_SOURCE_QUALITY", quality_ok, "verified event rests only on an interested source")

    age_ok = True
    precision_ok = True
    cutoff_ok = True
    for claim in claims:
        event_d = _parse_iso(claim.get("date"))
        stated = claim.get("age_stated")
        if stated is not None and birth and event_d:
            if stated != _age_on(birth, event_d):
                age_ok = False
        prec = claim.get("date_precision")
        if stated is not None and prec not in {"day", "month", None} and prec != "year":
            # year-only is honest only when age is constant all year
            if birth and event_d:
                jan = date(event_d.year, 1, 1)
                dec = date(event_d.year, 12, 31)
                if _age_on(birth, jan) != _age_on(birth, dec) and prec == "year":
                    precision_ok = False
        if cutoff and event_d and event_d > cutoff:
            cutoff_ok = False
        if event_d and event_d > date.today() and claim.get("type") == "event":
            cutoff_ok = False
    report.add("S6_AGE_ARITHMETIC", age_ok, "age_stated does not match birth_date on the event date")
    report.add("S7_PRECISION_HONESTY", precision_ok, "exact age asserted on a year-only date that crosses a birthday")
    report.add("S8_CUTOFF", cutoff_ok, "a claim is dated after fact_cutoff or in the unfinished future")

    rewind_quotes = [_script_norm(r.get("script_quote") or "") for r in rewinds]
    chrono_ok = True
    last = None
    for claim in claims:
        event_d = _parse_iso(claim.get("date"))
        if event_d is None:
            continue
        if last is not None and event_d < last:
            refs = " ".join(claim.get("script_refs") or [])
            if not any(q and q in _script_norm(refs) or q in script_n for q in rewind_quotes):
                chrono_ok = False
        last = event_d if last is None else max(last, event_d)
    report.add("S9_CHRONOLOGY", chrono_ok, "dates move backwards without a declared rewind")

    era_ok = True
    era_ranges: list[tuple[date, date, list[int], str]] = []
    for era in eras:
        start = _parse_iso(era.get("start"))
        end = _parse_iso(era.get("end"))
        ages = era.get("age_range") or [None, None]
        if start and end and start > end:
            era_ok = False
        if start and end:
            for other in era_ranges:
                if start <= other[1] and end >= other[0]:
                    era_ok = False
            era_ranges.append((start, end, list(ages), era.get("id") or ""))
        if birth and start and end and ages[0] is not None and ages[1] is not None:
            if _age_on(birth, start) != ages[0] or _age_on(birth, end) != ages[1]:
                era_ok = False
    for claim in claims:
        event_d = _parse_iso(claim.get("date"))
        era_id = claim.get("era_id")
        if event_d and era_id:
            match = next((e for e in era_ranges if e[3] == era_id), None)
            if match and not (match[0] <= event_d <= match[1]):
                era_ok = False
    report.add("S10_ERA_CONSISTENCY", era_ok, "eras overlap or a claim date sits outside its era")

    scene_era = True
    by_scene: dict[str, set[str]] = {}
    for claim in claims:
        era_id = claim.get("era_id") or ""
        for sid in claim.get("scene_refs") or []:
            by_scene.setdefault(sid, set()).add(era_id)
    for sid, era_ids in by_scene.items():
        era_ids.discard("")
        if len(era_ids) > 1:
            scene_era = False
    report.add("S11_SCENE_ERA_MATCH", scene_era, "one scene references claims from more than one era")

    qty_ok = True
    contested_ok = True
    for claim in claims:
        if claim.get("type") == "quantity" and (not claim.get("unit") or not claim.get("scope")):
            qty_ok = False
        if claim.get("certainty") == "contested":
            if not claim.get("conflict_note"):
                contested_ok = False
            refs = " ".join(claim.get("script_refs") or [])
            if refs and not HEDGE_RE.search(refs):
                contested_ok = False
    report.add("S12_QUANTITY_DEFINED", qty_ok, "quantity claim missing unit or scope")
    report.add("S13_CONTESTED_HANDLED", contested_ok, "contested claim lacks a conflict_note or hedge")

    span_ok = True
    if register.get("mode") == "REAL_PERSON":
        ages_stated = [c.get("age_stated") for c in claims if c.get("age_stated") is not None]
        start_age = register.get("title_start_age")
        end_age = register.get("title_end_age")
        if start_age is not None and start_age not in ages_stated:
            span_ok = False
        if end_age is not None and end_age not in ages_stated:
            span_ok = False
        if eras:
            latest = max(eras, key=lambda e: e.get("end") or "")
            last_third = script_n[int(len(script_n) * 2 / 3) :]
            latest_ids = [c.get("id") for c in claims if c.get("era_id") == latest.get("id")]
            if latest_ids and not any(
                any(ref in last_third for ref in (c.get("script_refs") or []))
                for c in claims
                if c.get("id") in latest_ids
            ):
                span_ok = False
    report.add("S14_SPAN_COVERED", span_ok, "title span or last-third latest-era claims are missing")

    ref_ok = True
    for claim in claims:
        for ref in claim.get("script_refs") or []:
            if script_n.count(_script_norm(ref)) != 1:
                ref_ok = False
    for rewind in rewinds:
        q = _script_norm(rewind.get("script_quote") or "")
        if q and script_n.count(q) != 1:
            ref_ok = False
    report.add("S15_REF_RESOLVES", ref_ok, "a script_ref matches zero or several places")

    covered = True
    sentences = re.split(r"(?<=[.!?])\s+", script_n)
    claim_blobs = " ".join(
        " ".join(c.get("script_refs") or []) for c in claims
    )
    for sentence in sentences:
        if QUANTITY_RE.search(sentence) and sentence not in claim_blobs and not any(
            ref in sentence for c in claims for ref in (c.get("script_refs") or [])
        ):
            covered = False
    report.add("S16_SPECIFICS_COVERED", covered, "a number in the script has no claim behind it")

    mind_hits = [s for s in sentences if MIND_RE.search(s)]
    backed = " ".join(
        " ".join(c.get("script_refs") or [])
        for c in claims
        if c.get("type") in {"quotation", "recollection", "interpretation"}
    )
    mind_unbacked = [s for s in mind_hits if s not in backed]
    report.add(
        "S17_MINDREADING_SCAN",
        not mind_unbacked,
        "; ".join(mind_unbacked[:3]),
        warning=True,
    )
    invent_hits = [s for s in sentences if INVENTION_RE.search(s)]
    invent_unbacked = [
        s
        for s in invent_hits
        if not any(ref in s for c in claims for ref in (c.get("script_refs") or []))
    ]
    report.add(
        "S18_INVENTION_SCAN",
        not invent_unbacked,
        "; ".join(invent_unbacked[:3]),
        warning=True,
    )
    return report


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Section 17B claims-register checks")
    p.add_argument("claims", help="claims_[slug].json")
    p.add_argument("script", help="clean script.txt")
    args = p.parse_args(argv)
    register = json.loads(Path(args.claims).read_text(encoding="utf-8"))
    script = Path(args.script).read_text(encoding="utf-8")
    report = validate_story(register, script)
    for check in report.checks:
        mark = "WARN" if check.warning and not check.ok else ("PASS" if check.ok else "FAIL")
        extra = f" — {check.detail}" if check.detail and not check.ok else ""
        print(f"{mark} {check.name}{extra}")
    return 0 if report.ok else 1


if __name__ == "__main__":
    sys.exit(main())
