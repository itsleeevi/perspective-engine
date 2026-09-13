"""Section 9B visual-fact checks."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

MARK_WORDS = (
    "crest",
    "badge",
    "sponsor",
    "signature",
    "autograph",
    "monogram",
    "logo",
)


@dataclass
class CheckResult:
    name: str
    ok: bool
    detail: str = ""
    warning: bool = False


@dataclass
class VisualReport:
    checks: list[CheckResult] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return all(c.ok or c.warning for c in self.checks)

    def add(self, name: str, ok: bool, detail: str = "", *, warning: bool = False) -> None:
        self.checks.append(CheckResult(name, ok, detail, warning=warning))


def _records(visual: dict) -> list[dict]:
    out: list[dict] = []
    for group in ("wardrobe", "appearance", "venues", "props"):
        for row in visual.get(group) or []:
            item = dict(row)
            item["_group"] = group
            out.append(item)
    return out


def validate_visual(
    visual: dict,
    prompts: list[str],
    *,
    scene_visuals: dict | None = None,
    protagonist_visible: list[bool] | None = None,
) -> VisualReport:
    report = VisualReport()
    rows = _records(visual)
    complete = True
    sourced = True
    uncertain = False
    pattern_ok = True
    for row in rows:
        if not row.get("id") or not row.get("label") or not row.get("tokens"):
            complete = False
        if row["_group"] in {"wardrobe", "venues"} and not row.get("valid_from") and not row.get("validity"):
            complete = False
        if not row.get("sources"):
            sourced = False
        if row.get("certainty") in {"uncertain", "contested"}:
            uncertain = True
        if row["_group"] == "wardrobe":
            tokens = " ".join(row.get("tokens") or [])
            if not any(w in tokens.lower() for w in ("hoop", "stripe", "plain", "trim", "collar", "cut", "pattern")):
                pattern_ok = False
    report.add("V1_RECORD_COMPLETE", complete, "a visual record is missing id, label, tokens, or a validity range")
    report.add("V2_VISUAL_FACTS_SOURCED", sourced, "a visual record has no source")
    report.add("V3_UNVERIFIED_FLAGGED", True, "uncertain visual records present", warning=uncertain)

    scene_map = (scene_visuals or {}).get("scenes") or scene_visuals or {}
    season_ok = True
    if isinstance(scene_map, dict):
        for sid, rec in scene_map.items():
            if not isinstance(rec, dict):
                continue
            wardrobe_id = rec.get("wardrobe")
            if wardrobe_id:
                hits = [r for r in rows if r.get("id") == wardrobe_id and r["_group"] == "wardrobe"]
                if len(hits) != 1:
                    season_ok = False
    report.add("V4_SEASON_RESOLVES", season_ok, "a scene does not resolve to exactly one wardrobe record")

    visible = protagonist_visible or [True] * len(prompts)
    facts_ok = True
    for prompt, shown in zip(prompts, visible):
        if not shown:
            continue
        for row in rows:
            if row["_group"] not in {"wardrobe", "appearance"}:
                continue
            for token in row.get("tokens") or []:
                if token not in prompt:
                    # Only require tokens tagged as default / always, or when scene_visuals pins the record.
                    if row.get("required_when_visible", True) and not scene_map:
                        facts_ok = False
    if scene_map and isinstance(scene_map, dict):
        facts_ok = True
        for prompt, shown in zip(prompts, visible):
            if not shown:
                continue
            # When a pin exists, only that record's tokens are required. Without per-prompt IDs,
            # require every token of every pinned wardrobe/appearance record to appear in at least
            # one visible prompt, and every visible prompt to carry each always-on appearance token.
            pass
        appearance_tokens = [
            t
            for r in rows
            if r["_group"] == "appearance"
            for t in (r.get("tokens") or [])
        ]
        for prompt, shown in zip(prompts, visible):
            if not shown:
                continue
            for token in appearance_tokens:
                if token not in prompt:
                    facts_ok = False
        pinned_ids = {
            rec.get("wardrobe")
            for rec in scene_map.values()
            if isinstance(rec, dict) and rec.get("wardrobe")
        }
        for wid in pinned_ids:
            rec = next((r for r in rows if r.get("id") == wid), None)
            if not rec:
                facts_ok = False
                continue
            blob = "\n".join(prompts)
            for token in rec.get("tokens") or []:
                if token not in blob:
                    facts_ok = False
    report.add("V5_PROMPT_CARRIES_FACTS", facts_ok, "an applicable visual token never reached a prompt")

    bans = [str(x).casefold() for x in (visual.get("bans") or [])]
    branding_ok = True
    for prompt in prompts:
        low = prompt.casefold()
        for ban in bans:
            if ban and ban in low:
                branding_ok = False
        if any(word in low for word in MARK_WORDS) and "no official club crests" not in low:
            # Asking to show a crest/badge/sponsor is the failure; the finishing ban sentence is allowed.
            if any(f"show {word}" in low or f"the {word}" in low for word in MARK_WORDS):
                branding_ok = False
    report.add("V6_NO_BRANDING", branding_ok, "a banned name or protected mark was requested")

    colors: dict[str, set[str]] = {}
    color_ok = True
    for row in rows:
        if row["_group"] != "wardrobe":
            continue
        era = row.get("era_id") or row.get("id")
        token_blob = " ".join(row.get("tokens") or []).lower()
        colors.setdefault(era, set()).add(token_blob)
    for era, variants in colors.items():
        if len(variants) > 1 and not any("validity" in str(r) or r.get("valid_from") for r in rows if r.get("era_id") == era or r.get("id") == era):
            color_ok = False
    report.add("V7_COLOR_CONSISTENCY", True, "same garment, different colours in one era", warning=not color_ok)
    report.add("V8_PATTERN_SPECIFIED", pattern_ok, "a wardrobe record names colours with no pattern or cut")
    return report


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Section 9B visual-fact checks")
    p.add_argument("visual_facts", help="visual_facts.json")
    p.add_argument("prompts", help="image-prompt file, one prompt per line with a blank line between")
    p.add_argument("--scene-visuals", default="")
    args = p.parse_args(argv)
    visual = json.loads(Path(args.visual_facts).read_text(encoding="utf-8"))
    raw = Path(args.prompts).read_text(encoding="utf-8")
    prompts = [block.strip() for block in raw.split("\n\n") if block.strip()]
    scene_visuals = None
    if args.scene_visuals:
        scene_visuals = json.loads(Path(args.scene_visuals).read_text(encoding="utf-8"))
    report = validate_visual(visual, prompts, scene_visuals=scene_visuals)
    for check in report.checks:
        mark = "WARN" if check.warning and not check.ok else ("PASS" if check.ok or check.warning else "FAIL")
        if check.warning and check.ok:
            mark = "WARN" if "uncertain" in check.detail or "colours" in check.detail else "PASS"
        extra = f" — {check.detail}" if check.detail and mark != "PASS" else ""
        print(f"{mark} {check.name}{extra}")
    return 0 if report.ok else 1


if __name__ == "__main__":
    sys.exit(main())
