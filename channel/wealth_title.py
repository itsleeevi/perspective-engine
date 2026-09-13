"""Parse Quiet Wealth POV titles. Default is a fictional illustrative story."""

from __future__ import annotations

import re

from channel.business_title import looks_like_money_engine, looks_like_wtrt
from channel.config import config_for
from channel.modes import ChannelMode
from channel.schema import SubjectStatus, TitleAnalysis
from channel.takeover_title import looks_like_takeover

_POV = re.compile(r"^POV:\s*(.+)$", re.IGNORECASE)
_YOU = re.compile(r"^You\s+(.+)$", re.IGNORECASE)
_YOU_ARE_AGE = re.compile(
    r"^You Are\s+(.+?)\s+From Age\s+(\d+)\s+to\s+(\d+)\s*$",
    re.IGNORECASE,
)
_YOU_ARE_TURN = re.compile(
    r"^You Are\s+([A-Z][\w.'-]+(?:\s+[A-Z][\w.'-]+)+)\.\s+(.+)$",
)
_YOU_ARE_NAME = re.compile(
    r"^You Are\s+([A-Z][\w.'-]+(?:\s+[A-Z][\w.'-]+)+)\s*$",
)
_EVERYONE = re.compile(
    r"^Everyone Thinks You(?:'re| are)\s+(.+?)(?:,|\.)?\s*"
    r"but You(?:'re| are)\s+(.+)$",
    re.IGNORECASE,
)
_WEALTH_MARKERS = (
    "pov:",
    "pov you",
    "stopped trying to look successful",
    "built wealth quietly",
    "could afford the upgrade",
    "turned down the raise",
    "quiet wealth",
)


def looks_like_wealth_pov(title: str) -> bool:
    raw = " ".join(title.strip().split())
    if _POV.match(raw):
        return True
    if looks_like_wtrt(raw) or looks_like_money_engine(raw) or looks_like_takeover(raw):
        return False
    lower = raw.lower()
    return any(m in lower for m in _WEALTH_MARKERS)


def analyze_wealth_title(
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
    if looks_like_takeover(raw) and not _POV.match(raw):
        raise ValueError(
            f"Title {title!r} is a How They Took Over title. "
            "Use --channel how_they_took_over."
        )
    cfg = config_for(ChannelMode.wealth_pov)
    body = raw
    pov = _POV.match(raw)
    if pov:
        body = pov.group(1).strip()
    elif not looks_like_wealth_pov(raw):
        raise ValueError(
            f"Title {title!r} does not match a Quiet Wealth POV pattern. "
            f"Example: {cfg.title_pattern!r}."
        )

    everyone = _EVERYONE.match(body)
    you = _YOU.match(body)
    if _YOU_ARE_AGE.match(body):
        m = _YOU_ARE_AGE.match(body)
        assert m is not None
        subject = m.group(1).strip()
        start_age, end_age = m.group(2), m.group(3)
        target = f"age {start_age} to {end_age}"
        question = (
            f"What happens when you live {subject}'s documented years "
            f"from age {start_age} to {end_age}?"
        )
        return TitleAnalysis(
            title=raw,
            subject=subject,
            target=target,
            verb=None,
            subject_status=SubjectStatus.living,
            category="documented life",
            relationship_type="sourced biography with original stand-in pictures",
            time_period=f"age {start_age} to {end_age}",
            core_question=question,
            research_priority="high",
            quotes_need_primary_sources=True,
            target_kind="wealth_pov",
            special_instructions=special_instructions,
            target_duration_seconds=target_duration_seconds
            or cfg.target_duration_seconds,
            channel_mode=ChannelMode.wealth_pov,
            company="",
            industry="",
            business_question="",
            apparent_business="",
            potential_hidden_engine="",
            customer="",
            likely_revenue_streams=[],
            business_model_complexity="",
            arena="",
            starting_position="",
            dominant_position="",
            likely_turning_points=[],
            potential_competitors=[],
            possible_hidden_advantage="",
        )
    if _YOU_ARE_TURN.match(body) or _YOU_ARE_NAME.match(body):
        turn = _YOU_ARE_TURN.match(body)
        named = _YOU_ARE_NAME.match(body)
        subject = (turn.group(1) if turn else named.group(1) if named else body).strip()
        target = turn.group(2).strip().rstrip(".") if turn else "the documented turning point"
        question = f"What happens when you live through {subject}'s documented {target}?"
        return TitleAnalysis(
            title=raw,
            subject=subject,
            target=target,
            verb=None,
            subject_status=SubjectStatus.living,
            category="documented life",
            relationship_type="sourced biography with original stand-in pictures",
            time_period="unknown until researched",
            core_question=question,
            research_priority="high",
            quotes_need_primary_sources=True,
            target_kind="wealth_pov",
            special_instructions=special_instructions,
            target_duration_seconds=target_duration_seconds
            or cfg.target_duration_seconds,
            channel_mode=ChannelMode.wealth_pov,
            company="",
            industry="",
            business_question="",
            apparent_business="",
            potential_hidden_engine="",
            customer="",
            likely_revenue_streams=[],
            business_model_complexity="",
            arena="",
            starting_position="",
            dominant_position="",
            likely_turning_points=[],
            potential_competitors=[],
            possible_hidden_advantage="",
        )
    if everyone:
        appearance = everyone.group(1).strip().rstrip(".")
        reality = everyone.group(2).strip().rstrip(".")
        subject = f"look {appearance}"
        target = reality
        question = (
            f"What happens when everyone thinks you are {appearance}, "
            f"but you are {reality}?"
        )
    elif you:
        rest = you.group(1).strip().rstrip("?").strip()
        if ". " in rest:
            first, second = rest.split(". ", 1)
            subject = first.strip()
            target = second.strip().rstrip(".")
        elif " and " in rest.lower():
            idx = rest.lower().index(" and ")
            subject = rest[:idx].strip()
            target = rest[idx + 5 :].strip().rstrip(".")
        else:
            subject = rest
            target = "the life that choice creates"
        spoken = subject[:1].lower() + subject[1:] if subject else subject
        question = f"What happens when you {spoken}?"
    else:
        subject = body.rstrip("?").strip()
        target = "the life that choice creates"
        question = f"What happens in the story promised by {raw}?"

    if not subject:
        raise ValueError(f"Title {title!r} has no POV choice to write.")
    return TitleAnalysis(
        title=raw,
        subject=subject,
        target=target,
        verb=None,
        subject_status=SubjectStatus.not_a_person,
        category="fictional wealth story",
        relationship_type="illustrative fiction unless a documented life is requested",
        time_period="unknown until planned",
        core_question=question,
        research_priority="medium",
        quotes_need_primary_sources=False,
        target_kind="wealth_pov",
        special_instructions=special_instructions,
        target_duration_seconds=target_duration_seconds
        or cfg.target_duration_seconds,
        channel_mode=ChannelMode.wealth_pov,
        company="",
        industry="",
        business_question="",
        apparent_business="",
        potential_hidden_engine="",
        customer="",
        likely_revenue_streams=[],
        business_model_complexity="",
        arena="",
        starting_position="",
        dominant_position="",
        likely_turning_points=[],
        potential_competitors=[],
        possible_hidden_advantage="",
    )
