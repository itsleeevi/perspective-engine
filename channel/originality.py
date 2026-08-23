"""Mass-production detector — compare a candidate cut to recent channel videos."""

from __future__ import annotations

import importlib.util
import json
import re
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

from channel.config import config_for
from channel.modes import ChannelMode, is_business, is_takeover, parse_mode
from channel.originality_policy import (
    BRAND_IGNORE_PATTERNS,
    GENERIC_SCENE_PATTERNS,
    MAX_SINGLE_DIMENSION_SIMILARITY,
    ORIGINALITY_SCORE_MIN,
    RECENT_VIDEO_COMPARE_COUNT,
    SIMILARITY_WEIGHTS,
    STOCK_ENDINGS,
    STOCK_HOOK_OPENERS,
    STOCK_TRANSITIONS,
)
from channel.paths import ROOT
from channel.schema import OriginalityReport, SimilarityBreakdown

_FIXTURES = ROOT / "fixtures"


class OriginalityError(RuntimeError):
    """Candidate cut is too similar to recent channel videos."""


def recent_slugs(
    *,
    limit: int | None = None,
    exclude: str | None = None,
    channel_mode: ChannelMode | str | None = None,
) -> list[str]:
    """Most recently indexed slugs for this channel (newest first)."""
    cap = limit or RECENT_VIDEO_COMPARE_COUNT
    index = ROOT / config_for(channel_mode).videos_index
    if not index.is_file():
        return []
    text = index.read_text(encoding="utf-8")
    slugs = re.findall(r"\]\(([a-z0-9-]+)\.md\)", text)
    out: list[str] = []
    for slug in slugs:
        if slug == "README":
            continue
        if exclude and slug == exclude:
            continue
        if slug not in out:
            out.append(slug)
        if len(out) >= cap:
            break
    return out


def _fixture_path(slug: str) -> Path | None:
    p = _FIXTURES / f"{slug}.json"
    return p if p.is_file() else None


def _spec_path(slug: str) -> Path | None:
    p = _FIXTURES / "video_specs" / f"{slug}.json"
    return p if p.is_file() else None


def _load_fixture(slug: str) -> dict | None:
    path = _fixture_path(slug)
    if not path:
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    return data if isinstance(data, dict) and "levels" in data else None


def _narration_of(fixture: dict) -> str:
    parts = [fixture.get("hook", "")]
    for level in fixture.get("levels", []):
        parts.extend(level.get("beats", []))
    return " ".join(p for p in parts if p)


def _chapter_names(fixture: dict) -> list[str]:
    return [
        str(level.get("name") or "").strip()
        for level in fixture.get("levels") or []
        if str(level.get("name") or "").strip()
    ]


def _hook(fixture: dict) -> str:
    return str(fixture.get("hook") or "").strip()


def _ending(fixture: dict) -> str:
    levels = fixture.get("levels") or []
    if not levels:
        return ""
    beats = levels[-1].get("beats") or []
    return str(beats[-1] if beats else "").strip()


def _ngrams(text: str, n: int = 4) -> set[tuple[str, ...]]:
    words = re.findall(r"[a-z']+", text.lower())
    return {tuple(words[i : i + n]) for i in range(len(words) - n + 1)}


def _strip_brand(text: str) -> str:
    out = text.lower()
    for pat in BRAND_IGNORE_PATTERNS:
        out = out.replace(pat, " ")
    return re.sub(r"\s+", " ", out).strip()


def _ratio(a: str, b: str) -> float:
    a, b = _strip_brand(a), _strip_brand(b)
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a, b).ratio() * 100.0


def _ngram_overlap_pct(a: str, b: str, n: int = 4) -> float:
    ga, gb = _ngrams(a, n), _ngrams(b, n)
    if not ga or not gb:
        return 0.0
    return len(ga & gb) / len(ga) * 100.0


def _structure_similarity(names_a: list[str], names_b: list[str]) -> float:
    if not names_a or not names_b:
        return 0.0
    joined_a = " | ".join(names_a).lower()
    joined_b = " | ".join(names_b).lower()
    seq = SequenceMatcher(None, joined_a, joined_b).ratio() * 100.0
    count_penalty = 100.0 - abs(len(names_a) - len(names_b)) * 8.0
    return max(seq, max(0.0, count_penalty * 0.3))


def _scene_tokens(slug: str) -> list[str]:
    spec = _spec_path(slug)
    if not spec:
        return []
    try:
        spec_data = json.loads(spec.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    module_path = ROOT / spec_data.get("stills_module", "")
    if not module_path.is_file():
        return []
    mspec = importlib.util.spec_from_file_location("stills_cmp", module_path)
    module = importlib.util.module_from_spec(mspec)
    assert mspec.loader is not None
    mspec.loader.exec_module(module)
    stills = list(getattr(module, "STILLS", []))
    tokens: list[str] = []
    for entry in stills:
        if len(entry) >= 3:
            shot, who, scene = entry[0], entry[1], entry[2]
            tokens.append(f"{shot}|{who}|{scene}".lower())
    return tokens


def _scene_sequence_similarity(tokens_a: list[str], tokens_b: list[str]) -> float:
    if not tokens_a or not tokens_b:
        return 0.0
    # Compare normalized location/prop tokens, not full prompts.
    def simplify(token: str) -> str:
        for pat in GENERIC_SCENE_PATTERNS:
            token = token.replace(pat, "GENERIC")
        return token

    sa = [simplify(t) for t in tokens_a]
    sb = [simplify(t) for t in tokens_b]
    return SequenceMatcher(None, sa, sb).ratio() * 100.0


def _visual_composition_similarity(tokens_a: list[str], tokens_b: list[str]) -> float:
    if not tokens_a or not tokens_b:
        return 0.0
    shots_a = [t.split("|", 1)[0] for t in tokens_a]
    shots_b = [t.split("|", 1)[0] for t in tokens_b]
    n = min(len(shots_a), len(shots_b), 40)
    if n == 0:
        return 0.0
    matches = sum(1 for i in range(n) if shots_a[i] == shots_b[i])
    return matches / n * 100.0


def _transition_similarity(text: str, corpus: list[str]) -> float:
    lower = text.lower()
    hits = sum(1 for phrase in STOCK_TRANSITIONS if phrase in lower)
    corpus_hits = sum(
        1 for phrase in STOCK_TRANSITIONS if any(phrase in c for c in corpus)
    )
    base = min(100.0, hits * 25.0)
    if corpus_hits >= 3 and hits:
        base = min(100.0, base + 15.0)
    return base


def _thumbnail_text(slug: str) -> str:
    spec = _spec_path(slug)
    if not spec:
        return ""
    try:
        data = json.loads(spec.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return ""
    return str((data.get("youtube") or {}).get("thumbnail_text") or "")


def _recent_narration_corpus(
    limit: int = 5, *, channel_mode: ChannelMode | str | None = None
) -> list[str]:
    out: list[str] = []
    for slug in recent_slugs(limit=limit, channel_mode=channel_mode):
        fixture = _load_fixture(slug)
        if fixture:
            out.append(_narration_of(fixture))
    return out


def compare_to_slug(candidate_slug: str, other_slug: str) -> SimilarityBreakdown | None:
    cand = _load_fixture(candidate_slug)
    other = _load_fixture(other_slug)
    if not cand or not other:
        return None
    narr_c = _narration_of(cand)
    narr_o = _narration_of(other)
    scenes_c = _scene_tokens(candidate_slug)
    scenes_o = _scene_tokens(other_slug)
    return SimilarityBreakdown(
        compared_slug=other_slug,
        hook=_ratio(_hook(cand), _hook(other)),
        phrasing=_ngram_overlap_pct(narr_c, narr_o),
        structure=_structure_similarity(_chapter_names(cand), _chapter_names(other)),
        scene_sequence=_scene_sequence_similarity(scenes_c, scenes_o),
        visual_composition=_visual_composition_similarity(scenes_c, scenes_o),
        transitions=_transition_similarity(
            narr_c, _recent_narration_corpus(channel_mode=_mode_for_slug(candidate_slug))
        ),
        conclusion=_ratio(_ending(cand), _ending(other)),
        thumbnail=_ratio(_thumbnail_text(candidate_slug), _thumbnail_text(other_slug)),
    )


def weighted_similarity(breakdown: SimilarityBreakdown) -> float:
    parts = {
        "hook": breakdown.hook,
        "phrasing": breakdown.phrasing,
        "structure": breakdown.structure,
        "scene_sequence": breakdown.scene_sequence,
        "visual_composition": breakdown.visual_composition,
        "transitions": breakdown.transitions,
        "conclusion": breakdown.conclusion,
        "thumbnail": breakdown.thumbnail,
    }
    return sum(parts[k] * SIMILARITY_WEIGHTS[k] for k in SIMILARITY_WEIGHTS)


def originality_score_from_similarity(avg_similarity: float) -> float:
    return max(0.0, min(100.0, 100.0 - avg_similarity))


def mode_for_slug(slug: str) -> ChannelMode:
    """Public alias: which channel a compiled slug belongs to."""
    return _mode_for_slug(slug)


def _mode_for_slug(slug: str) -> ChannelMode:
    spec = _spec_path(slug)
    if spec:
        try:
            data = json.loads(spec.read_text(encoding="utf-8"))
            raw = data.get("channel_mode")
            if raw:
                return parse_mode(raw)
        except (json.JSONDecodeError, OSError, ValueError):
            pass
    project = ROOT / "channel" / "projects" / slug / "project.json"
    if project.is_file():
        try:
            data = json.loads(project.read_text(encoding="utf-8"))
            raw = data.get("channel_mode")
            if raw:
                return parse_mode(raw)
        except (json.JSONDecodeError, OSError, ValueError):
            pass
    return ChannelMode.what_they_really_think


def originality_report_for_slug(slug: str) -> OriginalityReport:
    """Compare slug against recent videos on the same channel."""
    fixture = _load_fixture(slug)
    narration = _narration_of(fixture) if fixture else ""
    flags: list[str] = []
    comparisons: list[SimilarityBreakdown] = []
    mode = _mode_for_slug(slug)

    for other in recent_slugs(exclude=slug, channel_mode=mode):
        br = compare_to_slug(slug, other)
        if br:
            comparisons.append(br)

    if not comparisons:
        return OriginalityReport(
            slug=slug,
            originality_score=100.0,
            comparisons=[],
            flags=["no recent videos to compare — first cuts pass by default"],
            ready_for_images=True,
        )

    peak = max(weighted_similarity(c) for c in comparisons)
    avg = sum(weighted_similarity(c) for c in comparisons) / len(comparisons)
    score = originality_score_from_similarity(avg)

    worst = max(comparisons, key=weighted_similarity)
    if weighted_similarity(worst) > MAX_SINGLE_DIMENSION_SIMILARITY:
        flags.append(
            f"too close to {worst.compared_slug!r} "
            f"(weighted similarity {weighted_similarity(worst):.0f})"
        )

    if score < ORIGINALITY_SCORE_MIN:
        flags.append(
            f"originality_score {score:.0f} < {ORIGINALITY_SCORE_MIN} "
            f"(peak recent similarity {peak:.0f})"
        )

    lower = narration.lower()
    for phrase in STOCK_HOOK_OPENERS:
        if phrase in lower[:400]:
            flags.append(f"stock hook opener: {phrase!r}")
    for phrase in STOCK_ENDINGS:
        if phrase in lower[-800:]:
            flags.append(f"stock ending: {phrase!r}")

    thought = str((fixture or {}).get("the_thought") or "")
    if thought:
        for other in recent_slugs(
            exclude=slug, limit=RECENT_VIDEO_COMPARE_COUNT, channel_mode=mode
        ):
            other_fx = _load_fixture(other)
            if not other_fx:
                continue
            other_thought = str(other_fx.get("the_thought") or "")
            names = _names_from_title(
                str((fixture or {}).get("title") or ""),
                str(other_fx.get("title") or ""),
            )
            if other_thought and name_swap_too_close(thought, other_thought, names):
                flags.append(
                    f"name-swap spine: the_thought too close to {other!r} "
                    "after swapping the names"
                )

    if is_business(mode):
        from channel.originality_policy import BUSINESS_STOCK_HOOKS

        head = narration.lower()[:400]
        for phrase in BUSINESS_STOCK_HOOKS:
            if phrase in head:
                flags.append(f"stock business hook: {phrase!r} — vary the hook type")
    if is_takeover(mode):
        from channel.originality_policy import TAKEOVER_STOCK_HOOKS

        head = narration.lower()[:400]
        for phrase in TAKEOVER_STOCK_HOOKS:
            if phrase in head:
                flags.append(f"stock takeover hook: {phrase!r} — research must pick a different rise")

    # Generic scene grammar without historical reason.
    scenes = _scene_tokens(slug)
    if scenes:
        generic_hits = sum(
            1
            for tok in scenes
            if any(pat in tok for pat in GENERIC_SCENE_PATTERNS)
        )
        if generic_hits > len(scenes) * 0.35:
            flags.append(
                f"visual variety: {generic_hits}/{len(scenes)} scenes use "
                "desk/map/newspaper patterns — derive visuals from this title's events"
            )

    ready = score >= ORIGINALITY_SCORE_MIN and not any(
        "too close to" in f for f in flags
    )

    return OriginalityReport(
        slug=slug,
        originality_score=round(score, 1),
        mass_production_similarity=round(peak, 1),
        comparisons=comparisons,
        flags=flags,
        ready_for_images=ready,
    )


def assert_originality(slug: str, *, force: bool = False) -> OriginalityReport:
    report = originality_report_for_slug(slug)
    if force or report.ready_for_images:
        return report
    raise OriginalityError(
        "Originality QA failed for "
        f"{slug!r} (score {report.originality_score}, need "
        f"{ORIGINALITY_SCORE_MIN}). Flags: "
        + "; ".join(report.flags[:5])
        + ". Fix story/scenes/thumbnail, re-run "
        "`python -m channel originality <slug>`, or pass --force."
    )


def regenerate_targets(report: OriginalityReport) -> list[str]:
    """Which production stages to rewrite. Agents regenerate only these."""
    targets: list[str] = []

    def add(name: str) -> None:
        if name not in targets:
            targets.append(name)

    for flag in report.flags:
        lower = flag.lower()
        if "stock hook" in lower or "hook opener" in lower:
            add("hook")
        if "stock ending" in lower:
            add("ending")
        if "visual variety" in lower or "scene" in lower:
            add("scenes")
        if "too close to" in lower or "originality_score" in lower:
            add("story")
            add("narration")
            add("chapters")
        if "thumbnail" in lower:
            add("thumbnail")

    if report.comparisons and not report.ready_for_images:
        worst = max(report.comparisons, key=weighted_similarity)
        if worst.hook >= 50:
            add("hook")
        if worst.phrasing >= 15:
            add("narration")
        if worst.structure >= 60:
            add("chapters")
        if worst.scene_sequence >= 40 or worst.visual_composition >= 70:
            add("scenes")
        if worst.conclusion >= 70:
            add("ending")
        if worst.thumbnail >= 70:
            add("thumbnail")
        if worst.transitions >= 40:
            add("narration")

    if not report.ready_for_images and not targets:
        add("story")
        add("narration")
    return targets


def _names_from_title(*titles: str) -> list[str]:
    names: list[str] = []
    for title in titles:
        raw = title.strip()
        m = re.match(
            r"What (.+?) Really (?:Thought|Thinks) About (.+)$",
            raw,
            re.I,
        )
        if m:
            names.extend(p.strip() for p in m.groups() if p.strip())
            continue
        m = re.match(r"^(?:How|Why)\s+(.+?)(?:\s+Really\b|\s+Makes\b|\s+Is\b|\s+Does\b|$)", raw, re.I)
        if m:
            names.append(m.group(1).strip())
    return names


def name_swap_too_close(text_a: str, text_b: str, names: list[str]) -> bool:
    """True if swapping the people would leave basically the same sentence."""
    def strip(text: str) -> str:
        out = text.lower()
        for name in names:
            if name:
                out = re.sub(rf"\b{re.escape(name.lower())}\b", "name", out)
        return re.sub(r"\s+", " ", out).strip()

    a, b = strip(text_a), strip(text_b)
    if not a or not b:
        return False
    if a == b:
        return True
    return SequenceMatcher(None, a, b).ratio() >= 0.85


def slug_from_spec(spec: dict[str, Any], *, short: bool = False) -> str:
    from channel.cadence import slug_from_spec as _cadence_slug

    return _cadence_slug(spec, short=short)


def originality_report_for_spec(spec_path: Path | str) -> OriginalityReport:
    spec = json.loads(Path(spec_path).read_text(encoding="utf-8"))
    slug = slug_from_spec(spec)
    return originality_report_for_slug(slug)
