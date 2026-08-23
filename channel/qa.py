"""Retention / visual / payoff QA that can run without an LLM."""

from __future__ import annotations

import re

from channel.config import CHANNEL, config_for_project
from channel.modes import is_business
from channel.originality_policy import GENERIC_AI_PHRASES, STOCK_ENDINGS, STOCK_TRANSITIONS
from channel.schema import QaScores, VideoProject


_BORN = re.compile(r"\b(was|were)\s+born\b", re.I)
_PHOTO = re.compile(
    r"\b(photorealistic|hyperrealistic|cinematic photography|3d render|anime|"
    r"oil painting|watercolor|ultra realistic|dslr|photograph|realistic skin)\b",
    re.I,
)


def narration_of(project: VideoProject) -> str:
    if not project.story:
        return ""
    parts = [project.story.hook, *[c.narration for c in project.story.chapters]]
    if project.story.next_video_bridge:
        parts.append(project.story.next_video_bridge)
    return " ".join(p for p in parts if p)


def word_count(text: str) -> int:
    return len(re.findall(r"\S+", text))


def first_n_seconds_words(n: float, project: VideoProject | None = None) -> int:
    wpm = config_for_project(project).narration_wpm if project else CHANNEL.narration_wpm
    return max(8, int(wpm * (n / 60.0)))


def mechanical_qa(project: VideoProject) -> QaScores:
    """Deterministic flags. The Cursor agent still assigns 1–10 scores."""
    notes: list[str] = []
    text = narration_of(project)
    words = word_count(text)
    scores = QaScores()
    cfg = config_for_project(project)

    if not project.story:
        notes.append("no story yet")
        return scores.model_copy(update={"notes": notes})

    if words < cfg.narration_word_min:
        notes.append(f"narration is {words} words (min {cfg.narration_word_min})")
        scores.pacing = 4
    elif words > cfg.narration_word_max:
        notes.append(f"narration is {words} words (max {cfg.narration_word_max})")
        scores.pacing = 6
    else:
        scores.pacing = 8

    head = " ".join(text.split()[: first_n_seconds_words(15, project)])
    if _BORN.search(head):
        notes.append("cold open starts with a birth — rewrite; that is a biography")
        scores.hook = 3
    elif is_business(project.channel_mode) and re.search(
        r"\b(was|were)\s+founded\b", head, re.I
    ):
        notes.append("cold open starts with a founding — start with the contradiction")
        scores.hook = 3
    else:
        scores.hook = 8

    first30 = " ".join(text.split()[: first_n_seconds_words(30, project)])
    if project.analysis.subject.lower() not in first30.lower():
        notes.append("first 30s never names the subject")
        scores.curiosity = 5
    if not is_business(project.channel_mode):
        target_word = project.analysis.target.split()[0].lower()
        if target_word not in first30.lower():
            notes.append("first 30s never names the target")
            scores.curiosity = min(scores.curiosity or 8, 5)
    if "?" not in first30 and not re.search(r"\b(but|except|yet|why)\b", first30, re.I):
        notes.append("first 30s has no question or contradiction")
        scores.curiosity = min(scores.curiosity or 8, 5)
    if scores.curiosity == 0:
        scores.curiosity = 8

    payoff = project.story.title_payoff.strip()
    if payoff and payoff.lower().rstrip(".") not in text.lower():
        notes.append("title_payoff is not spoken in the narration")
        scores.title_payoff = 3
    elif payoff:
        scores.title_payoff = 8
    else:
        notes.append("missing title_payoff")
        scores.title_payoff = 2

    if not project.story.major_contradiction.strip():
        notes.append("no major_contradiction")
        scores.contradiction = 3
    else:
        scores.contradiction = 8

    if not project.story.next_video_bridge.strip():
        notes.append("no next-video bridge")
        scores.ending = 5
    else:
        scores.ending = 8

    lower = text.lower()
    for phrase in (*cfg.banned_written_register, *GENERIC_AI_PHRASES):
        if phrase in lower:
            notes.append(f"written-register phrase: {phrase!r}")
            scores.clarity = 5
    for phrase in STOCK_TRANSITIONS:
        if phrase in lower:
            notes.append(f"stock transition: {phrase!r} — write one this event owns")
            scores.clarity = min(scores.clarity or 8, 5)
    tail = " ".join(text.split()[-80:]).lower()
    for phrase in STOCK_ENDINGS:
        if phrase in tail:
            notes.append(f"stock ending: {phrase!r} — pick a different ending strategy")
            scores.ending = min(scores.ending or 8, 4)
    if scores.clarity == 0:
        scores.clarity = 8

    if project.scenes:
        vis_notes = visual_qa(project)
        notes.extend(vis_notes)
        scores.visual_potential = 5 if vis_notes else 8
    else:
        notes.append("no scenes yet")
        scores.visual_potential = 8

    # Story/emotion need a human pass. Mechanical QA only fails measured gaps.
    if scores.story == 0:
        scores.story = 5 if any("biography" in n or "title_payoff" in n for n in notes) else 8
    if scores.emotional_variety == 0:
        scores.emotional_variety = 8
    scores.notes = notes
    return scores


def visual_qa(project: VideoProject) -> list[str]:
    notes: list[str] = []
    types: list[str] = []
    for scene in project.scenes:
        types.append(scene.visual_type or scene.composition)
        blob = f"{scene.action} {scene.composition}"
        if _PHOTO.search(blob) and "not " not in blob.lower():
            notes.append(f"{scene.scene_id}: photoreal/cinematic language in the action")
        for cid in scene.characters:
            if cid not in project.characters:
                notes.append(f"{scene.scene_id}: unknown character id {cid}")
        if scene.location and scene.location not in project.locations:
            notes.append(f"{scene.scene_id}: unknown location id {scene.location}")
        if scene.who != "empty" and not scene.characters and scene.who == "hero":
            if not any(c.is_subject for c in project.characters.values()):
                notes.append(f"{scene.scene_id}: hero shot but no subject character")
    for person in project.characters.values():
        lock = person.visual_lock or ""
        if person.historical_name and person.historical_name.lower() in lock.lower():
            notes.append(f"{person.id}: visual_lock contains historical_name")
    if types:
        top = max(types.count(t) for t in set(types))
        if top > max(4, len(types) * 0.4):
            notes.append("shot types repeat too often — rotate composition")
    return notes


def thirty_second_blocks(project: VideoProject) -> list[str]:
    words = narration_of(project).split()
    cfg = config_for_project(project)
    n = first_n_seconds_words(cfg.retention_block_seconds, project)
    blocks = []
    for i in range(0, len(words), n):
        chunk = " ".join(words[i : i + n])
        if chunk:
            blocks.append(chunk)
    return blocks


def run_full_qa(project: VideoProject):
    """Factcheck + retention + originality + monetization. Persist on the project."""
    from channel.factcheck import factcheck
    from channel.monetization_qa import compute_monetization_readiness
    from channel.originality import originality_report_for_slug

    report = factcheck(project.research, channel_mode=project.channel_mode)
    project.factcheck = report
    project.qa = mechanical_qa(project)
    if is_business(project.channel_mode):
        from channel.business_qa import mechanical_business_qa

        project.business_qa = mechanical_business_qa(project)
        project.qa.notes.extend(project.business_qa.notes)
    try:
        originality = originality_report_for_slug(project.slug)
    except Exception:
        originality = None
    project.originality = originality
    project.monetization = compute_monetization_readiness(project, originality)
    return report, project.qa, originality, project.monetization


def title_payoff_ok(project: VideoProject) -> bool:
    if not project.story:
        return False
    return bool(project.story.title_payoff.strip()) and project.story.title_payoff.lower().rstrip(".") in narration_of(project).lower()
