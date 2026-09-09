"""Quiet Wealth QA — fiction ledger, six chapters, second-person POV."""

from __future__ import annotations

import re

from channel.config import config_for_project
from channel.qa import narration_of, word_count
from channel.schema import VideoProject, WealthQaReport

_YOU = re.compile(r"\byou\b", re.I)
_SECOND = re.compile(r"\b(you|your|you're|you've|you'll|you'd)\b", re.I)


def mechanical_wealth_qa(project: VideoProject) -> WealthQaReport:
    notes: list[str] = []
    text = narration_of(project)
    words = word_count(text)
    cfg = config_for_project(project)
    report = WealthQaReport()

    if not project.story:
        notes.append("no story yet")
        report.notes = notes
        return report

    if cfg.narration_word_min <= words <= cfg.narration_word_max:
        report.pacing = 8
    elif words:
        report.pacing = 4
        notes.append(
            f"narration is {words} words "
            f"(target {cfg.narration_word_min}–{cfg.narration_word_max})"
        )

    you_hits = len(_SECOND.findall(text))
    if you_hits < 8:
        notes.append("narration is not clearly second-person POV")
        report.story_depth = 4
    else:
        report.story_depth = 8

    chapters = project.story.chapters
    if not (cfg.chapter_count_min <= len(chapters) <= cfg.chapter_count_max):
        notes.append(
            f"{len(chapters)} chapters — Quiet Wealth uses "
            f"{cfg.chapter_count_min} named levels"
        )
        report.story_depth = min(report.story_depth, 5)
    names = [c.name.strip().lower() for c in chapters]
    if len(names) != len(set(names)):
        notes.append("chapter names repeat — each level needs a different function")
        report.story_depth = min(report.story_depth, 5)

    ctx = project.wealth
    if ctx is None:
        notes.append("missing project.wealth ledger / character notes")
        report.ledger = 3
    else:
        bits = 0
        if ctx.core_tension:
            bits += 1
        if ctx.signature_object:
            bits += 1
        if ctx.job or ctx.income_situation:
            bits += 1
        if ctx.ledger_notes:
            bits += 1
        if ctx.supporting_characters:
            bits += 1
        if ctx.places:
            bits += 1
        report.ledger = min(10, 4 + bits)
        if ctx.fictional is False and not project.research.claims:
            notes.append("non-fiction episode has no sourced claims")
            report.ledger = min(report.ledger, 4)

    if project.story.title_payoff.strip() and project.story.title_payoff.lower().rstrip(
        "."
    ) in text.lower():
        report.title_payoff = 8
    else:
        report.title_payoff = 3
        notes.append("title_payoff / the_thought is missing from the VO")

    if _YOU.search(" ".join(text.split()[:80]) or ""):
        report.hook = 8
    else:
        report.hook = 5
        notes.append("opening does not address the viewer as you")

    report.curiosity = 8 if "?" in text[:800] or re.search(
        r"\b(but|instead|except)\b", text[:800], re.I
    ) else 5
    report.visual_variety = 8
    report.notes = notes
    report.ready = (
        report.pacing >= 8
        and report.story_depth >= 8
        and report.ledger >= 8
        and report.title_payoff >= 8
        and not notes
    )
    return report
