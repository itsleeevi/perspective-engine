"""Retention / visual / payoff QA that can run without an LLM."""

from __future__ import annotations

import re

from channel.config import CHANNEL
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


def first_n_seconds_words(n: float) -> int:
    return max(8, int(CHANNEL.narration_wpm * (n / 60.0)))


def mechanical_qa(project: VideoProject) -> QaScores:
    """Deterministic flags. The Cursor agent still assigns 1–10 scores."""
    notes: list[str] = []
    text = narration_of(project)
    words = word_count(text)
    scores = QaScores()

    if not project.story:
        notes.append("no story yet")
        return scores.model_copy(update={"notes": notes})

    if words < CHANNEL.narration_word_min:
        notes.append(f"narration is {words} words (min {CHANNEL.narration_word_min})")
        scores.pacing = 4
    elif words > CHANNEL.narration_word_max:
        notes.append(f"narration is {words} words (max {CHANNEL.narration_word_max})")
        scores.pacing = 6
    else:
        scores.pacing = 8

    head = " ".join(text.split()[: first_n_seconds_words(15)])
    if _BORN.search(head):
        notes.append("cold open starts with a birth — rewrite; that is a biography")
        scores.hook = 3
    else:
        scores.hook = 8

    first30 = " ".join(text.split()[: first_n_seconds_words(30)])
    if project.analysis.subject.lower() not in first30.lower():
        notes.append("first 30s never names the subject")
        scores.curiosity = 5
    if project.analysis.target.split()[0].lower() not in first30.lower():
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
    for phrase in CHANNEL.banned_written_register:
        if phrase in lower:
            notes.append(f"written-register phrase: {phrase!r}")
            scores.clarity = 5
    if scores.clarity == 0:
        scores.clarity = 8

    if project.scenes:
        vis_notes = visual_qa(project)
        notes.extend(vis_notes)
        scores.visual_potential = 5 if vis_notes else 8
    else:
        notes.append("no scenes yet")
        scores.visual_potential = 4

    if scores.story == 0:
        scores.story = 7 if notes else 8
    if scores.emotional_variety == 0:
        scores.emotional_variety = 7
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
    n = first_n_seconds_words(CHANNEL.retention_block_seconds)
    blocks = []
    for i in range(0, len(words), n):
        chunk = " ".join(words[i : i + n])
        if chunk:
            blocks.append(chunk)
    return blocks


def title_payoff_ok(project: VideoProject) -> bool:
    if not project.story:
        return False
    return bool(project.story.title_payoff.strip()) and project.story.title_payoff.lower().rstrip(".") in narration_of(project).lower()
