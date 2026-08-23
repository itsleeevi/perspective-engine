"""Parse How They Took Over titles. Do not assume the strategic bet."""

from __future__ import annotations

import re

from channel.business_title import (
    _COMPANY_SUFFIXES,
    _HOW,
    _TITLE_PREDICATES,
    _WHY,
    looks_like_money_engine,
    looks_like_wtrt,
)
from channel.config import config_for
from channel.modes import ChannelMode
from channel.schema import SubjectStatus, TitleAnalysis

_TOOK_OVER = re.compile(
    r"^How\s+(.+?)\s+(?:Quietly\s+)?Took Over\s+(.+)$",
    re.IGNORECASE,
)
_WHY_USING = re.compile(
    r"^Why Everyone Started Using\s+(.+)$",
    re.IGNORECASE,
)
_TAKEOVER_MARKERS = (
    "took over",
    "built an empire",
    "became so powerful",
    "became the",
    "became a",
    "won the",
    "beat everyone",
    "became the standard",
    "changed an entire",
    "quietly took over",
    "everyone started using",
    "global giant",
    "cult following",
    "status symbol",
    "impossible to compete",
    "impossible to ignore",
)
_TAKEOVER_PREDICATES = _TITLE_PREDICATES | {
    "took",
    "won",
    "made",
    "created",
    "destroyed",
    "went",
    "beat",
    "changed",
    "quietly",
}

_UNKNOWN = "unknown until researched"


def looks_like_takeover(title: str) -> bool:
    raw = " ".join(title.strip().split())
    if looks_like_wtrt(raw) or looks_like_money_engine(raw):
        return False
    lower = raw.lower()
    if _TOOK_OVER.match(raw) or _WHY_USING.match(raw):
        return True
    return any(m in lower for m in _TAKEOVER_MARKERS)


def _subject_and_rest(body: str) -> tuple[str, str]:
    body = body.strip().rstrip("?").strip()
    parts = body.split()
    if not parts:
        return body, ""
    i = 0
    while i < len(parts):
        tok = parts[i].lower().rstrip(".,")
        if i > 0 and tok in _TAKEOVER_PREDICATES:
            break
        i += 1
        while i < len(parts) and parts[i].lower().rstrip(".") in {
            s.rstrip(".") for s in _COMPANY_SUFFIXES
        }:
            i += 1
    if i == 0:
        i = 1
    subject = " ".join(parts[:i]).strip(" '\"")
    rest = " ".join(parts[i:]).strip()
    return subject or body, rest


_DID_VERBS = {
    "became": "become",
    "built": "build",
    "took": "take",
    "won": "win",
    "made": "make",
    "created": "create",
    "destroyed": "destroy",
    "went": "go",
    "changed": "change",
    "quietly": "quietly",
}


def _spoken_rest(rest: str) -> str:
    parts = rest.split(None, 1)
    if not parts:
        return rest
    first = _DID_VERBS.get(parts[0].lower(), parts[0].lower())
    return f"{first} {parts[1]}" if len(parts) > 1 else first


def analyze_takeover_title(
    title: str,
    *,
    special_instructions: str = "",
    target_duration_seconds: int | None = None,
) -> TitleAnalysis:
    raw = " ".join(title.strip().split())
    if looks_like_wtrt(raw):
        raise ValueError(
            f"Title {title!r} is a What They Really Think title. "
            "Use --channel what_they_really_think."
        )
    if looks_like_money_engine(raw):
        raise ValueError(
            f"Title {title!r} is a How They Really Make Money title. "
            "Use --channel behind_the_business."
        )
    cfg = config_for(ChannelMode.how_they_took_over)
    took = _TOOK_OVER.match(raw)
    why_using = _WHY_USING.match(raw)
    how = _HOW.match(raw)
    why = _WHY.match(raw)
    if took:
        subject = took.group(1).strip()
        arena = took.group(2).strip().rstrip("?").strip()
        question = f"How did {subject} take over {arena}?"
        target = arena
    elif why_using:
        subject = why_using.group(1).strip().rstrip("?").strip()
        arena = _UNKNOWN
        question = f"Why did everyone start using {subject}?"
        target = "widespread adoption"
    elif how:
        subject, rest = _subject_and_rest(how.group(1))
        arena = rest or _UNKNOWN
        question = (
            f"How did {subject} {_spoken_rest(rest)}?"
            if rest
            else f"How did {subject} take over?"
        )
        target = rest or "the category"
    elif why:
        subject, rest = _subject_and_rest(why.group(1))
        arena = rest or _UNKNOWN
        question = (
            f"Why did {subject} {_spoken_rest(rest)}?"
            if rest
            else f"Why did {subject} win?"
        )
        target = rest or "this rise"
    else:
        raise ValueError(
            f"Title {title!r} does not match a How They Took Over pattern "
            f"(How / Why…). Example: {cfg.title_pattern!r}."
        )
    if not subject:
        raise ValueError(f"Title {title!r} has no subject to research.")
    return TitleAnalysis(
        title=raw,
        subject=subject,
        target=target,
        verb=None,
        subject_status=SubjectStatus.not_a_person,
        category="technology/business",
        relationship_type=_UNKNOWN,
        time_period=_UNKNOWN,
        core_question=question,
        research_priority="high",
        quotes_need_primary_sources=True,
        target_kind="takeover",
        special_instructions=special_instructions,
        target_duration_seconds=target_duration_seconds or cfg.target_duration_seconds,
        channel_mode=ChannelMode.how_they_took_over,
        company=subject,
        industry=_UNKNOWN,
        arena=arena if arena else _UNKNOWN,
        starting_position=_UNKNOWN,
        dominant_position=_UNKNOWN,
        likely_turning_points=[],
        potential_competitors=[],
        possible_hidden_advantage=_UNKNOWN,
    )
