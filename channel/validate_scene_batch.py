"""Section 17A mechanical checks for a life-POV scene batch.

Call with the selected source, the two batch files, and a JSON ledger of
id / start / end offsets into the normalized source.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

from channel.life_pov_blocks import (
    ABSENCE,
    BATCH_SIZE,
    EM_DASH,
    FINISHING,
    FINISHING_TEXT_ALLOWED_MID,
    FINISHING_TEXT_ALLOWED_PREFIX,
    FINISHING_TEXT_ALLOWED_SUFFIX,
    SKIN_LOCK_PREFIX,
    SKIN_LOCK_SUFFIX,
    STYLE_OBJECT,
    STYLE_PEOPLE,
)

CUE_RE = re.compile(r"\[(\d{2,}:\d{2}(?:\.\d+)?)[a-z]?\]")
PLACEMENT_RE = re.compile(
    r'^\[(?P<id>[^\]]+)\] IMAGE: (?P<image>.+) SHOW FROM: "(?P<show>.*)" KEEP UNTIL: "(?P<keep>.*)"$'
)
PROMPT_ID_RE = re.compile(r"^\[(?P<id>[^\]]+)\] (?P<body>.+)$")
HEADING_RE = re.compile(r"^(#|\*\*|```|\{|\[\{|- )")


@dataclass
class CheckResult:
    name: str
    ok: bool
    detail: str = ""


@dataclass
class SceneLedgerRow:
    id: str
    start: int
    end: int


@dataclass
class BatchReport:
    checks: list[CheckResult] = field(default_factory=list)
    ids: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return all(c.ok for c in self.checks)

    def add(self, name: str, ok: bool, detail: str = "") -> None:
        self.checks.append(CheckResult(name, ok, detail))


def normalize(
    text: str,
    *,
    strip_cues: bool = False,
    artifact_removals: list[str] | None = None,
) -> str:
    """Section 0 NORMALIZATION only, plus confirmed cue / artifact removals."""
    raw = text.replace("\r\n", "\n").replace("\r", "\n")
    if strip_cues:
        raw = CUE_RE.sub(" ", raw)
    for token in artifact_removals or []:
        if token:
            raw = raw.replace(token, " ")
    joined = " ".join(line.strip() for line in raw.split("\n") if line.strip())
    return " ".join(joined.split()).strip()


def _split_entries(text: str) -> list[str]:
    body = text.replace("\r\n", "\n").replace("\r", "\n")
    if body.startswith("\n"):
        body = body[1:]
    body = body.rstrip("\n")
    if not body:
        return []
    return body.split("\n\n")


def load_ledger(path: Path) -> list[SceneLedgerRow]:
    data = json.loads(path.read_text(encoding="utf-8"))
    rows = data["scenes"] if isinstance(data, dict) and "scenes" in data else data
    out: list[SceneLedgerRow] = []
    for row in rows:
        out.append(
            SceneLedgerRow(
                id=str(row["id"]),
                start=int(row["start"]),
                end=int(row["end"]),
            )
        )
    return out


def _style_ok(body: str) -> bool:
    return body.startswith(STYLE_PEOPLE) or body.startswith(STYLE_OBJECT)


def _has_skin_lock(body: str) -> bool:
    i = body.find(SKIN_LOCK_PREFIX)
    if i < 0:
        return False
    return SKIN_LOCK_SUFFIX in body[i:]


def _has_absence(body: str) -> bool:
    return ABSENCE in body


def _has_finishing(body: str) -> bool:
    if FINISHING in body:
        return True
    i = body.find(FINISHING_TEXT_ALLOWED_PREFIX)
    if i < 0:
        return False
    rest = body[i + len(FINISHING_TEXT_ALLOWED_PREFIX) :]
    mid = rest.find(FINISHING_TEXT_ALLOWED_MID)
    if mid < 0:
        return False
    tail = rest[mid + len(FINISHING_TEXT_ALLOWED_MID) :]
    return FINISHING_TEXT_ALLOWED_SUFFIX in tail


def _block_fidelity(body: str) -> bool:
    if not _style_ok(body):
        return False
    if not _has_finishing(body):
        return False
    skin = _has_skin_lock(body)
    absent = _has_absence(body)
    if skin == absent:
        return False
    return True


def validate_scene_batch(
    source_text: str,
    prompt_text: str,
    placement_text: str,
    ledger: list[SceneLedgerRow],
    *,
    strip_cues: bool = False,
    artifact_removals: list[str] | None = None,
    banned: set[str] | None = None,
    batch_size: int = BATCH_SIZE,
    final_batch: bool = False,
    prior_ids: set[str] | None = None,
) -> BatchReport:
    report = BatchReport()
    source = normalize(
        source_text, strip_cues=strip_cues, artifact_removals=artifact_removals
    )
    prompt_entries = _split_entries(prompt_text)
    place_entries = _split_entries(placement_text)

    prompt_ids: list[str] = []
    prompt_bodies: list[str] = []
    prompt_shape_ok = True
    for entry in prompt_entries:
        if "\n" in entry or HEADING_RE.match(entry or ""):
            prompt_shape_ok = False
        m = PROMPT_ID_RE.match(entry)
        if not m:
            prompt_shape_ok = False
            prompt_ids.append("")
            prompt_bodies.append(entry)
            continue
        prompt_ids.append(m.group("id"))
        prompt_bodies.append(m.group("body"))

    place_ids: list[str] = []
    place_fields: list[re.Match[str] | None] = []
    field_shape_ok = True
    for entry in place_entries:
        if "\n" in entry or HEADING_RE.match(entry or ""):
            field_shape_ok = False
        m = PLACEMENT_RE.match(entry)
        if not m:
            field_shape_ok = False
            place_ids.append("")
            place_fields.append(None)
            continue
        place_ids.append(m.group("id"))
        place_fields.append(m)

    report.ids = prompt_ids
    report.add("ID_MATCH", prompt_ids == place_ids, f"{prompt_ids!r} vs {place_ids!r}")
    unique = len(prompt_ids) == len(set(prompt_ids)) and all(prompt_ids)
    report.add("ID_UNIQUE", unique, "duplicate or empty scene ID")
    prior = prior_ids or set()
    overlap = [i for i in prompt_ids if i in prior]
    report.add("ID_CONTINUITY", not overlap, f"reused IDs: {overlap}")

    trailing_blanks = prompt_text.endswith("\n\n\n") or placement_text.endswith("\n\n\n")
    report.add(
        "LINE_SHAPE",
        prompt_shape_ok
        and all("\n" not in e for e in place_entries)
        and not trailing_blanks
        and "```" not in prompt_text
        and "```" not in placement_text,
        "heading, fence, multi-line entry, or extra trailing blanks",
    )
    report.add("FIELD_SHAPE", field_shape_ok, "placement line is not ID / IMAGE / SHOW FROM / KEEP UNTIL")

    anchor_exact = True
    anchor_unique = True
    bleed_ok = True
    if len(ledger) != len(place_fields):
        anchor_exact = False
    else:
        prev_end = 0
        for row, match in zip(ledger, place_fields, strict=True):
            if match is None:
                anchor_exact = False
                continue
            show = match.group("show")
            keep = match.group("keep")
            span = source[row.start : row.end]
            if not span.startswith(show) or not span.rstrip().endswith(keep):
                anchor_exact = False
            if source.count(show) != 1:
                anchor_unique = False
            if source.count(keep) != 1:
                anchor_unique = False
            if row.start < prev_end:
                bleed_ok = False
            prev_end = row.end

    report.add("ANCHOR_EXACT", anchor_exact, "SHOW FROM / KEEP UNTIL do not sit on the span edges")
    report.add("ANCHOR_UNIQUE", anchor_unique, "lengthen a repeated anchor until it occurs once")
    report.add("NO_ANCHOR_BLEED", bleed_ok, "a KEEP UNTIL overlaps the next SHOW FROM")

    coverage = False
    reconstruct = False
    if ledger:
        ordered = sorted(ledger, key=lambda r: r.start)
        contiguous = ordered[0].start == 0 or not final_batch
        if final_batch:
            contiguous = ordered[0].start == 0
        for a, b in zip(ordered, ordered[1:]):
            if a.end != b.start:
                contiguous = False
        ends_ok = ordered[-1].end == len(source) if final_batch else ordered[-1].end <= len(source)
        if not final_batch and ordered[0].start != 0:
            # Continuation batches start where the previous batch ended.
            contiguous = all(a.end == b.start for a, b in zip(ordered, ordered[1:]))
        coverage = contiguous and ends_ok and all(0 <= r.start <= r.end <= len(source) for r in ledger)
        rebuilt = "".join(source[r.start : r.end] for r in ledger)
        assigned = source[ledger[0].start : ledger[-1].end] if ledger else ""
        reconstruct = rebuilt == assigned
    report.add("COVERAGE", coverage, "gaps or overlaps in the offset ledger")
    report.add("RECONSTRUCT", reconstruct, "concatenated spans do not reproduce the assigned source")

    banned_hits: list[str] = []
    for body in prompt_bodies:
        if EM_DASH in body:
            banned_hits.append("em dash")
        if "SHOW FROM" in body or "KEEP UNTIL" in body:
            banned_hits.append("placement fields in prompt")
        if "[" in body or "]" in body:
            banned_hits.append("inner brackets")
        for token in banned or set():
            if token and token.casefold() in body.casefold():
                banned_hits.append(token)
    report.add("BANNED_IN_PROMPTS", not banned_hits, ", ".join(sorted(set(banned_hits))))

    required_ok = True
    for body in prompt_bodies:
        style_n = int(STYLE_PEOPLE in body) + int(STYLE_OBJECT in body)
        finish_n = int(FINISHING in body) + int(FINISHING_TEXT_ALLOWED_PREFIX in body)
        presence_n = int(_has_skin_lock(body)) + int(_has_absence(body))
        if style_n != 1 or finish_n != 1 or presence_n != 1:
            required_ok = False
    report.add(
        "REQUIRED_IN_PROMPTS",
        required_ok,
        "need exactly one STYLE, one FINISHING, and one of SKIN_LOCK or ABSENCE",
    )
    report.add(
        "BLOCK_FIDELITY",
        all(_block_fidelity(b) for b in prompt_bodies) if prompt_bodies else False,
        "a block was paraphrased or both presence modules appear",
    )

    planned = len(ledger) if ledger else len(prompt_ids)
    counts_ok = len(prompt_ids) == len(place_ids) == planned
    if final_batch:
        size_ok = 1 <= planned <= batch_size
    else:
        size_ok = planned == batch_size
    report.add("COUNTS", counts_ok and size_ok, f"prompts={len(prompt_ids)} placement={len(place_ids)} planned={planned}")

    encoding_ok = EM_DASH not in prompt_text and EM_DASH not in placement_text
    for match in place_fields:
        if match is None:
            continue
        for quote in (match.group("show"), match.group("keep")):
            if "\u201c" in quote or "\u201d" in quote:
                encoding_ok = False
    report.add("ENCODING", encoding_ok, "em dash or smart quotes that the source does not use")
    return report


def _load_banned(path: Path | None) -> set[str]:
    if path is None:
        return set()
    tokens: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        token = line.strip()
        if token and not token.startswith("#"):
            tokens.add(token)
    return tokens


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Section 17A scene-batch checks")
    p.add_argument("source", help="selected source transcript")
    p.add_argument("prompts", help="batch_NN_image_prompts_slug.txt")
    p.add_argument("placement", help="batch_NN_scene_placement_slug.txt")
    p.add_argument("ledger", help="JSON list of {id, start, end}")
    p.add_argument("--strip-cues", action="store_true")
    p.add_argument("--final-batch", action="store_true")
    p.add_argument("--banned", default="", help="file of banned names, one per line")
    p.add_argument("--batch-size", type=int, default=BATCH_SIZE)
    args = p.parse_args(argv)
    report = validate_scene_batch(
        Path(args.source).read_text(encoding="utf-8"),
        Path(args.prompts).read_text(encoding="utf-8"),
        Path(args.placement).read_text(encoding="utf-8"),
        load_ledger(Path(args.ledger)),
        strip_cues=args.strip_cues,
        banned=_load_banned(Path(args.banned) if args.banned else None),
        batch_size=args.batch_size,
        final_batch=args.final_batch,
    )
    for check in report.checks:
        mark = "PASS" if check.ok else "FAIL"
        extra = f" — {check.detail}" if check.detail and not check.ok else ""
        print(f"{mark} {check.name}{extra}")
    return 0 if report.ok else 1


if __name__ == "__main__":
    sys.exit(main())
