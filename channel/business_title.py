"""Parse Behind The Business titles. Do not guess the hidden engine."""

from __future__ import annotations

import re

from channel.config import config_for
from channel.modes import ChannelMode
from channel.schema import SubjectStatus, TitleAnalysis

_WTRT = re.compile(
    r"^What\s+.+?\s+Really\s+(Thought|Thinks)\s+About\s+.+?\s*\??$",
    re.IGNORECASE,
)
_HOW = re.compile(r"^How\s+(.+)$", re.IGNORECASE)
_WHY = re.compile(r"^Why\s+(.+)$", re.IGNORECASE)
_THE = re.compile(
    r"^The\s+(?:Business Behind|Hidden Economics of|Strange Business Model Behind|"
    r"Business of)\s+(.+)$",
    re.IGNORECASE,
)
_MAKES_MONEY = re.compile(
    r"^(.+?)\s+(?:Really\s+)?Makes? Money(?:\s+From\s+(.+?))?(?:\s+(.+))?$",
    re.IGNORECASE,
)


def looks_like_wtrt(title: str) -> bool:
    return bool(_WTRT.match(" ".join(title.strip().split())))


def looks_like_business(title: str) -> bool:
    raw = " ".join(title.strip().split())
    return bool(_HOW.match(raw) or _WHY.match(raw) or _THE.match(raw))


_COMPANY_SUFFIXES = frozenset(
    {"inc", "inc.", "corp", "corp.", "co", "co.", "company", "llc", "ltd", "ltd."}
)

# The predicate that starts the rest of a How/Why title. Do not treat these
# as part of a multi-word company ("Credit Card Companies Really…").
_TITLE_PREDICATES = frozenset(
    {
        "really",
        "makes",
        "became",
        "is",
        "does",
        "keeps",
        "built",
        "turned",
        "turn",
        "can",
        "wants",
        "want",
        "barely",
        "intentionally",
        "love",
        "loves",
        "sold",
        "sells",
    }
)


def _possessive(name: str) -> str:
    return f"{name}'" if name.endswith(("s", "S")) else f"{name}'s"


def _company_and_rest(body: str) -> tuple[str, str]:
    """Company is the prefix before the title predicate (Really / Makes / Is…)."""
    body = body.strip().rstrip("?").strip()
    parts = body.split()
    if not parts:
        return body, ""
    i = 0
    while i < len(parts):
        tok = parts[i].lower().rstrip(".,")
        if i > 0 and tok in _TITLE_PREDICATES:
            break
        i += 1
        while i < len(parts) and parts[i].lower().rstrip(".") in {
            s.rstrip(".") for s in _COMPANY_SUFFIXES
        }:
            i += 1
    if i == 0:
        i = 1
    company = " ".join(parts[:i]).strip(" '\"")
    rest = " ".join(parts[i:]).strip()
    return company or body, rest


def analyze_business_title(
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
    cfg = config_for(ChannelMode.behind_the_business)
    how = _HOW.match(raw)
    why = _WHY.match(raw)
    the = _THE.match(raw)
    if how:
        company, rest = _company_and_rest(how.group(1))
        money = _MAKES_MONEY.match(f"{company} {rest}".strip())
        if money:
            company = money.group(1).strip()
            from_what = (money.group(2) or "").strip()
            trailing = (money.group(3) or "").strip()
            extra = from_what or trailing
            if from_what:
                question = f"How does {company} make money from {from_what}?"
            elif trailing:
                question = f"How does {company} make money {trailing}?"
            else:
                question = f"Where does {_possessive(company)} economic profit actually come from?"
            target = extra or "how the company makes money"
        else:
            question = f"How does {company} {rest}?" if rest else f"How does {company} work?"
            target = rest or "the business model"
    elif why:
        company, rest = _company_and_rest(why.group(1))
        question = f"Why does {company} {rest}?" if rest else f"Why does {company} work this way?"
        target = rest or "this strategy"
    elif the:
        company = the.group(1).strip().rstrip("?").strip()
        question = f"What is the real business behind {company}?"
        target = "the real business"
    else:
        raise ValueError(
            f"Title {title!r} does not match a Behind The Business pattern "
            f"(How / Why / The Business Behind…). Example: "
            f"{cfg.title_pattern!r}."
        )
    if not company:
        raise ValueError(f"Title {title!r} has no company to research.")
    return TitleAnalysis(
        title=raw,
        subject=company,
        target=target,
        verb=None,
        subject_status=SubjectStatus.not_a_person,
        category="business",
        relationship_type="unknown until researched",
        time_period="unknown until researched",
        core_question=question,
        research_priority="high",
        quotes_need_primary_sources=True,
        target_kind="business_model",
        special_instructions=special_instructions,
        target_duration_seconds=target_duration_seconds or cfg.target_duration_seconds,
        channel_mode=ChannelMode.behind_the_business,
        company=company,
        industry="unknown until researched",
        business_question=question,
        apparent_business="unknown until researched",
        potential_hidden_engine="unknown until researched",
        customer="unknown until researched",
        likely_revenue_streams=[],
        business_model_complexity="unknown until researched",
    )
