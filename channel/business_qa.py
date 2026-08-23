"""Behind The Business retention, claim, and virality QA."""

from __future__ import annotations

import re

from channel.config import config_for_project
from channel.modes import ChannelMode
from channel.qa import first_n_seconds_words, narration_of, word_count
from channel.schema import BusinessQaReport, VideoProject

_DEAD = (
    ("long company history", re.compile(r"\b(was founded in|born in \d{4}|childhood)\b", re.I)),
    ("number dump", re.compile(r"(\$[\d,.]+\b.*){3,}", re.I)),
    ("generic industry", re.compile(r"\bthe industry as a whole\b|\bin today's market\b", re.I)),
    ("mba jargon", re.compile(r"\bleverages?\b|\bsynergies\b|\bvertically integrated economies\b", re.I)),
    ("slow founder biography", re.compile(r"\bgrew up in\b|\bas a young (man|woman|child)\b", re.I)),
    ("abstract finance", re.compile(r"\brecurring revenue dynamics\b|\beconomies of scale in conjunction\b", re.I)),
)

_EXAGGERATION = re.compile(
    r"\b(most profitable|the largest|dominates|a monopoly|nearly all|"
    r"everyone|never loses money|guaranteed to grow|will explode)\b",
    re.I,
)
_INVESTMENT = re.compile(
    r"\b(buy this stock|sell this stock|you should invest|this stock will)\b",
    re.I,
)
_STOCK_BTB_HOOK = re.compile(
    r"this company (isn'?t|is not) really .{1,40}\.\s+it'?s actually",
    re.I,
)
_MONEY = re.compile(
    r"\$[\d,.]+(?:\s*(?:billion|million|trillion))?"
    r"|\b\d{1,3}(?:\.\d+)?\s*%"
    r"|\b(?:revenue|profit|margin|subscribers?|valuation)\b.{0,40}\b\d",
    re.I,
)


def sixty_second_segments(project: VideoProject) -> list[str]:
    words = narration_of(project).split()
    n = first_n_seconds_words(60, project)
    return [" ".join(words[i : i + n]) for i in range(0, len(words), n) if words[i : i + n]]


def dead_section_flags(text: str) -> list[str]:
    hits = []
    for label, pat in _DEAD:
        if pat.search(text):
            hits.append(label)
    return hits


def claim_exaggeration_flags(project: VideoProject) -> list[str]:
    flags: list[str] = []
    text = narration_of(project)
    for m in _EXAGGERATION.finditer(text):
        phrase = m.group(0)
        flags.append(f"exaggeration needs evidence or qualification: {phrase!r}")
    if _INVESTMENT.search(text):
        flags.append("investment advice — rewrite; this channel explains businesses")
    for claim in project.research.claims:
        if _MONEY.search(claim.claim) and not claim.sources:
            flags.append(f"{claim.claim_id}: financial figure has no source")
        if _MONEY.search(claim.claim) and not (claim.fiscal_period or project.research.fiscal_period):
            flags.append(f"{claim.claim_id}: financial figure missing fiscal_period")
        if claim.calculation and not claim.inputs and not claim.sources:
            flags.append(f"{claim.claim_id}: derived number has no inputs or sources")
    return flags


def five_minute_gaps(project: VideoProject) -> list[str]:
    """Flag 5-minute windows that never shift (no question / but / so)."""
    words = narration_of(project).split()
    n = first_n_seconds_words(300, project)
    gaps: list[str] = []
    markers = re.compile(r"\b(but|yet|so|why|except|instead|the strange|the real)\b", re.I)
    for i, start in enumerate(range(0, len(words), n)):
        chunk = " ".join(words[start : start + n])
        if chunk and not markers.search(chunk):
            gaps.append(f"~{i * 5} min: no reveal / shift / new question")
    return gaps


def weak_minute_flags(project: VideoProject) -> list[str]:
    weak: list[str] = []
    for i, segment in enumerate(sixty_second_segments(project), start=1):
        if len(segment.split()) < 20:
            continue
        learns = bool(
            re.search(
                r"\b(because|so|that means|the reason|instead|but|profit|fee|member)\b",
                segment,
                re.I,
            )
        )
        next_reason = "?" in segment or bool(
            re.search(r"\b(why|but|so what|the strange|another question)\b", segment, re.I)
        )
        if not learns:
            weak.append(f"minute {i}: no new thing learned")
        if not next_reason:
            weak.append(f"minute {i}: no reason to watch the next minute")
    return weak


def mechanical_business_qa(project: VideoProject) -> BusinessQaReport:
    """Deterministic BTB flags. The agent still assigns editorial 1–10s."""
    notes: list[str] = []
    text = narration_of(project)
    cfg = config_for_project(project)
    words = word_count(text)
    report = BusinessQaReport()
    if project.channel_mode != ChannelMode.behind_the_business:
        report.notes = ["not a Behind The Business project"]
        return report
    if words and words < cfg.narration_word_min:
        notes.append(f"narration is {words} words (min {cfg.narration_word_min})")
        report.pacing = 4
    elif words > cfg.narration_word_max:
        notes.append(
            f"narration is {words} words (max {cfg.narration_word_max}) — cut, do not pad"
        )
        report.pacing = 6
    else:
        report.pacing = 8

    head = " ".join(text.split()[: first_n_seconds_words(30, project)])
    if re.search(r"\bwas founded\b|\bwere founded\b", head, re.I):
        notes.append("cold open starts with a founding date — start with the contradiction")
        report.hook = 3
    elif _STOCK_BTB_HOOK.search(head):
        notes.append("stock 'isn't really X, it's actually Y' hook — vary the hook type")
        report.hook = 5
    else:
        report.hook = 8

    company = (project.analysis.company or project.analysis.subject).lower()
    if company and company not in head.lower():
        notes.append("first 30s never names the company")
        report.curiosity = 5
    if "?" not in head and not re.search(r"\b(but|except|yet|why)\b", head, re.I):
        notes.append("first 30s has no question or contradiction")
        report.curiosity = min(report.curiosity or 8, 5)
    if report.curiosity == 0:
        report.curiosity = 8

    payoff = (project.story.title_payoff if project.story else "").strip()
    if payoff and payoff.lower().rstrip(".") in text.lower():
        report.title_payoff = 8
    else:
        report.title_payoff = 3
        notes.append("title payoff missing from narration")

    report.dead_sections = dead_section_flags(text)
    report.weak_minutes = weak_minute_flags(project) + five_minute_gaps(project)
    report.claim_flags = claim_exaggeration_flags(project)
    if report.dead_sections:
        notes.extend(f"dead section: {d}" for d in report.dead_sections)
        report.story_depth = 5
    else:
        report.story_depth = 8
    if report.weak_minutes:
        notes.extend(report.weak_minutes[:6])
        report.pacing = min(report.pacing or 8, 5)
    if report.claim_flags:
        notes.extend(report.claim_flags[:6])
        report.business_surprise = 5
    else:
        report.business_surprise = 8

    types = [s.visual_type for s in project.scenes if s.visual_type]
    if types and len(set(types)) < 4:
        notes.append("visual types too few — rotate diagrams, stores, money flow, maps")
        report.visual_variety = 5
    elif project.scenes:
        report.visual_variety = 8
    else:
        report.visual_variety = 6
        notes.append("no scenes yet")

    if project.story and project.story.next_video_bridge.strip():
        report.related_video_potential = 8
    else:
        report.related_video_potential = 4
        notes.append("no related-company bridge")

    report.title_strength = 8 if project.title else 2
    thumb = (project.metadata.thumbnail_text if project.metadata else "").strip()
    thumb_words = len(thumb.split())
    if thumb and 2 <= thumb_words <= 5:
        report.thumbnail_concept = 8
    elif thumb:
        report.thumbnail_concept = 4
        notes.append("thumbnail_text should be 2–5 words, not the full title")
    else:
        report.thumbnail_concept = 5
    report.notes = notes
    report.ready = (
        report.hook >= 8
        and report.curiosity >= 8
        and report.story_depth >= 8
        and report.title_payoff >= 8
        and not report.claim_flags
        and not any("minute" in w for w in report.weak_minutes)
    )
    return report
