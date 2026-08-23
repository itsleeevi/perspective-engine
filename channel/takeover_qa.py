"""How They Took Over retention, claim, and virality QA."""

from __future__ import annotations

import re

from channel.config import config_for_project
from channel.modes import ChannelMode
from channel.qa import first_n_seconds_words, narration_of, word_count
from channel.schema import TakeoverQaReport, VideoProject

_DEAD = (
    ("long founder biography", re.compile(r"\b(grew up in|as a young (man|woman|child)|childhood)\b", re.I)),
    ("generic corporate history", re.compile(r"\bwas founded in\b.{0,40}\b(then|later)\b.{0,80}\blaunched\b", re.I)),
    ("product list", re.compile(r"\b(product line included|their products were|they released)\b.{0,80},.{0,80},.{0,80}and\b", re.I)),
    ("mba jargon", re.compile(r"\bleverages?\b|\bsynergies\b|\bsustained competitive advantage\b|\bvertically integrated economies\b", re.I)),
    ("slow market background", re.compile(r"\bin today's market\b|\bthe industry as a whole\b|\bthroughout the sector\b", re.I)),
    ("abstract strategy", re.compile(r"\bfrom a strategic standpoint\b|\bthis demonstrates that\b|\bit should be noted\b", re.I)),
    ("generic rise template", re.compile(
        r"\bsmall (?:company|startup)\b.{0,200}\b(idea|product)\b.{0,200}\blaunch",
        re.I | re.S,
    )),
)

_EXAGGERATION = re.compile(
    r"\b(destroyed everyone|shocking move|a monopoly|never loses|"
    r"impossible to stop forever|guaranteed to grow|will explode)\b",
    re.I,
)
_INVESTMENT = re.compile(
    r"\b(buy this stock|sell this stock|you should invest|this stock will)\b",
    re.I,
)
_MONEY = re.compile(
    r"\$[\d,.]+(?:\s*(?:billion|million|trillion))?"
    r"|\b\d{1,3}(?:\.\d+)?\s*%"
    r"|\b(?:revenue|profit|margin|market share)\b.{0,40}\b\d",
    re.I,
)
_UNKNOWN = "unknown until researched"


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
        flags.append(f"exaggeration needs evidence or qualification: {m.group(0)!r}")
    if _INVESTMENT.search(text):
        flags.append("investment advice — rewrite; this channel explains a rise")
    for claim in project.research.claims:
        if _MONEY.search(claim.claim) and not claim.sources:
            flags.append(f"{claim.claim_id}: financial figure has no source")
        if _MONEY.search(claim.claim) and not (
            claim.fiscal_period or project.research.fiscal_period or claim.date
        ):
            flags.append(f"{claim.claim_id}: financial figure missing fiscal_period")
        if claim.calculation and not claim.inputs and not claim.sources:
            flags.append(f"{claim.claim_id}: derived number has no inputs or sources")
    return flags


def five_minute_gaps(project: VideoProject) -> list[str]:
    words = narration_of(project).split()
    n = first_n_seconds_words(300, project)
    gaps: list[str] = []
    markers = re.compile(
        r"\b(but|yet|so|why|except|instead|the bet|the war|the flywheel|"
        r"competitors?|turning point|pulled away)\b",
        re.I,
    )
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
                r"\b(because|so|that means|the reason|instead|but|then|"
                r"competitors?|flywheel|bet|advantage)\b",
                segment,
                re.I,
            )
        )
        next_reason = "?" in segment or bool(
            re.search(
                r"\b(why|but|so what|the strange|another question|then)\b",
                segment,
                re.I,
            )
        )
        if not learns:
            weak.append(f"minute {i}: no new thing learned")
        if not next_reason:
            weak.append(f"minute {i}: no reason to watch the next minute")
    return weak


def mechanical_takeover_qa(project: VideoProject) -> TakeoverQaReport:
    """Deterministic HTTO flags. The agent still assigns editorial 1–10s."""
    notes: list[str] = []
    text = narration_of(project)
    cfg = config_for_project(project)
    words = word_count(text)
    report = TakeoverQaReport()
    if project.channel_mode != ChannelMode.how_they_took_over:
        report.notes = ["not a How They Took Over project"]
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
        notes.append("cold open starts with a founding date — start with the transformation gap")
        report.hook = 3
    elif re.search(r"\bwas born\b|\bwere born\b", head, re.I):
        notes.append("cold open starts with a birth — that is a biography")
        report.hook = 3
    else:
        report.hook = 8

    subject = (project.analysis.subject or project.analysis.company).lower()
    if subject and subject not in head.lower():
        notes.append("first 30s never names the subject")
        report.curiosity = 5
    if "?" not in head and not re.search(r"\b(but|except|yet|why|today)\b", head, re.I):
        notes.append("first 30s has no question or surprising gap")
        report.curiosity = min(report.curiosity or 8, 5)
    if report.curiosity == 0:
        report.curiosity = 8

    ctx = project.takeover
    start = (ctx.starting_position if ctx else "") or ""
    now = (ctx.current_position if ctx else "") or ""
    if start and now and start != _UNKNOWN and now != _UNKNOWN and start.lower() != now.lower():
        report.transformation = 8
    else:
        report.transformation = 4
        notes.append("takeover starting_position / current_position still unknown — research the gap")

    if ctx and ctx.turning_points:
        report.turning_points = 8
    else:
        report.turning_points = 4
        notes.append("no ranked turning points")

    if ctx and ctx.competitors:
        report.competition = 8
    else:
        report.competition = 4
        notes.append("no competitor map")

    payoff = (project.story.title_payoff if project.story else "").strip()
    if payoff and payoff.lower().rstrip(".") in text.lower():
        report.title_payoff = 9 if report.transformation >= 8 else 8
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

    types = [s.visual_type for s in project.scenes if s.visual_type]
    if types and len(set(types)) < 4:
        notes.append("visual types too few — rotate flywheels, wars, maps, origins, threats")
        report.visual_variety = 5
    elif project.scenes:
        report.visual_variety = 8
    else:
        report.visual_variety = 6
        notes.append("no scenes yet")

    if project.story and project.story.next_video_bridge.strip():
        report.related_video_potential = 8
    elif ctx and ctx.related_subject.strip():
        report.related_video_potential = 7
        notes.append("related_subject set but no spoken next-video bridge")
    else:
        report.related_video_potential = 4
        notes.append("no related-takeover bridge")

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
        and report.title_payoff >= 9
        and report.transformation >= 8
        and not report.claim_flags
        and not any("minute" in w for w in report.weak_minutes)
    )
    return report
