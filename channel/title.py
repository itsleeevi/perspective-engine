"""Agent 1 — Title Analyzer.

Parses the channel's title pattern in code. Research still has to decide
the answer; this stage only names the question.
"""

from __future__ import annotations

import re

from channel.business_title import analyze_business_title, looks_like_business
from channel.config import CHANNEL, config_for
from channel.modes import ChannelMode, parse_mode
from channel.schema import SubjectStatus, TitleAnalysis

_TITLE = re.compile(
    r"^What\s+(.+?)\s+Really\s+(Thought|Thinks)\s+About\s+(.+?)\s*\??$",
    re.IGNORECASE,
)


def analyze_title(
    title: str,
    *,
    special_instructions: str = "",
    target_duration_seconds: int | None = None,
    channel_mode: ChannelMode | str | None = None,
) -> TitleAnalysis:
    raw = " ".join(title.strip().split())
    mode = parse_mode(channel_mode)
    if mode is ChannelMode.behind_the_business:
        return analyze_business_title(
            raw,
            special_instructions=special_instructions,
            target_duration_seconds=target_duration_seconds,
        )
    m = _TITLE.match(raw)
    if not m:
        hint = ""
        if looks_like_business(raw):
            hint = (
                " If this is a Behind The Business title, pass "
                "--channel behind_the_business."
            )
        raise ValueError(
            f"Title {title!r} does not match '{CHANNEL.title_pattern}'. "
            "Example: 'What Einstein Really Thought About Religion'."
            f"{hint}"
        )
    subject, verb, target = m.group(1).strip(), m.group(2).title(), m.group(3).strip()
    verb = "Thinks" if verb.lower() == "thinks" else "Thought"
    status = SubjectStatus.living if verb == "Thinks" else SubjectStatus.unknown
    core = f"What did {subject} really think about {target}?"
    if verb == "Thinks":
        core = f"What does {subject} really think about {target}?"
    return TitleAnalysis(
        title=raw,
        subject=subject,
        target=target,
        verb=verb,  # type: ignore[arg-type]
        subject_status=status,
        core_question=core,
        special_instructions=special_instructions,
        target_duration_seconds=target_duration_seconds
        or config_for(mode).target_duration_seconds,
        channel_mode=ChannelMode.what_they_really_think,
    )
