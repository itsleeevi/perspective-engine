"""
Story linter — machine-checks that a new cut's script is NEW and SPOKEN,
before any stills or audio exist.

    .venv/bin/python scripts/lint_story.py fixtures/video_specs/<slug>.json

"Every new title gets a completely new story" is enforced here, not trusted
to whichever model wrote the script:

1. NOVELTY   — 4-gram overlap of the new narration against every other
               fixture in fixtures/. More than 10% shared with a shipped
               script means the model recycled a spine; rewrite.
2. MOTIFS    — every docs/videos/<slug>.md keeps a "## Do not copy" section;
               any quoted phrase from those sections that reappears in the
               new narration is an error. The banned list grows by itself as
               videos ship.
2b. ENGINE   — new channel cuts may not reuse another fixture's chapter
               cards, a too-close the_thought, or the "Month Year. Name…"
               cold-open stamp. Each title needs its own story engine.
3. NARRATOR  — third person only. Narrator-"I" ("I will count the fakes")
               and lecture numbering ("fake number one", "level two") are
               errors.
4. SPOKEN    — telegram-fragment share capped (short sentences are punches,
               not the default register); zero contractions is flagged as
               written-not-spoken English.
4b. EXPLAIN-LIKE-FIVE — fixture must have ``the_thought`` (≤22 words, a
               child could repeat it) and that sentence must appear in the VO.
4c. YEARS    — channel cuts write calendar years as digits (1995). Captions
               show digits; Kokoro speaks the year. Spelled-out years fail
               (shipped Jobs-Gates is grandfathered).
4d. CLOCK    — research through the day you write. Do not say "today is
               DATE", "as of today", "this morning", or "ten days ago".
4e. ADVISOR  — this channel tells a history story. It does not give
               medical, legal, or investment advice in the VO.
4f. ORIGINALITY — compare against the last 10 shipped videos
               (`scripts/lint_originality.py`). Score must be >= 80.
               Stock AI transitions / hook templates / interchangeable
               name-swap spines fail. Rewrite the flagged sections.
5. STRUCTURE — hook present; 4-6 silent chapter cards with poster-like
               names (<= 4 words) when title_style is "chapter".

Exit 1 on any ERROR. A cheap execution model loops write -> lint -> rewrite
until this passes; that loop is what makes cheap-model scripts shippable.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from adapters.voice.years import SPELLED_YEAR
from channel.config import config_for
from channel.modes import is_business
from channel.originality import mode_for_slug
from channel.originality_policy import GENERIC_AI_PHRASES

ROOT = Path(__file__).resolve().parent.parent

# Shipped channel cuts that still spell years in the fixture. Do not rewrite
# them — captions and stills already match that VO. New titles must use digits.
_WORD_YEAR_GRANDFATHERED = frozenset(
    {
        "steve-jobs-bill-gates",
        "steve-jobs-bill-gates_short",
    }
)

# Research through the day you write. Do not pin the VO to "today is DATE".
_PRODUCTION_CLOCK = re.compile(
    r"\bas of today\b|"
    r"\btoday is [a-z]+ \d{1,2}\b|"
    r"\btoday[,]?\s+(?:january|february|march|april|may|june|july|august|"
    r"september|october|november|december)\b|"
    r"\byesterday[,]?\s+(?:january|february|march|april|may|june|july|august|"
    r"september|october|november|december)\b|"
    r"\bten days ago\b|"
    r"\bthis morning\b",
    re.I,
)


def production_clock_hit(text: str) -> str | None:
    """Return the first 'today is DATE' style phrase, if any."""
    m = _PRODUCTION_CLOCK.search(text or "")
    return m.group(0) if m else None


# Illustrated history, not an AI doctor / lawyer / advisor.
_ADVISOR_VOICE = re.compile(
    r"\byou should invest\b|"
    r"\binvest your (?:money|savings|portfolio)\b|"
    r"\bbuy this (?:stock|coin|token)\b|"
    r"\bconsult (?:a|your) (?:doctor|lawyer|attorney|physician)\b|"
    r"\bsee (?:a|your) (?:doctor|lawyer|attorney)\b|"
    r"\bas your (?:doctor|lawyer|attorney|financial advisor)\b|"
    r"\byour legal rights\b|"
    r"\btake this (?:pill|supplement|remedy|medication)\b|"
    r"\bhere is how to (?:sue|invest|diagnose|treat)\b|"
    r"\bthis is financial advice\b|"
    r"\bthis is medical advice\b|"
    r"\bthis is legal advice\b",
    re.I,
)


def advisor_voice_hit(text: str) -> str | None:
    """Return the first narrator-as-advisor phrase, if any."""
    m = _ADVISOR_VOICE.search(text or "")
    return m.group(0) if m else None


def generic_ai_hit(text: str) -> str | None:
    """Return the first generic-AI essay phrase, if any."""
    lower = (text or "").lower()
    for phrase in GENERIC_AI_PHRASES:
        if phrase in lower:
            return phrase
    return None


# Shipped channel cuts written before uniqueness-of-engine checks.
# Do not rewrite them. New titles must invent a new spine.
_UNIQUENESS_GRANDFATHERED = frozenset(
    {
        "elon-musk-ai",
        "jeff-bezos-elon-musk",
        "sam-altman-the-future-of-work",
        "steve-jobs-bill-gates",
        "einstein-religion",
        "einstein-zionism",
        "stalin_hitler",
        "hitler_americans",
        "putin_americans",
        "kremlin_americans",
    }
)

# Shipped ~8-minute channel cuts. New titles must hit 4400–5500 words.
_LENGTH_GRANDFATHERED = frozenset(
    {
        "elon-musk-ai",
        "jeff-bezos-elon-musk",
        "sam-altman-the-future-of-work",
        "steve-jobs-bill-gates",
        "einstein-religion",
        "einstein-zionism",
        "darwin-human-nature",
        "stalin_hitler",
        "hitler_americans",
        "putin_americans",
        "kremlin_americans",
    }
)

_GENERIC_CHAPTERS = frozenset({"the short", "the link", "intro"})
_THE_ONE_WORD = re.compile(r"^The [A-Z][a-z]+$")
_MONTH_YEAR_STAMP = re.compile(
    r"^(january|february|march|april|may|june|july|august|september|"
    r"october|november|december)\s+\d{4}\.",
    re.I,
)
_THOUGHT_STOP = frozenset(
    "he she they his her their a an the and or but to of in on for with as "
    "is was were be been being that this it not really thinks thought about".split()
)


def chapter_names(fixture: dict) -> list[str]:
    return [
        str(level.get("name") or "").strip()
        for level in fixture.get("levels") or []
        if str(level.get("name") or "").strip()
    ]


def hook_is_month_year_stamp(hook: str) -> bool:
    """True when the cold open is the recycled 'February 2026. Name…' stamp."""
    return bool(_MONTH_YEAR_STAMP.match((hook or "").strip()))


def thought_content_words(text: str) -> set[str]:
    return {
        w
        for w in re.findall(r"[a-z']+", (text or "").lower())
        if w not in _THOUGHT_STOP
    }


def thoughts_too_close(left: str, right: str) -> bool:
    """True when two title-payoffs share most of their content words."""
    a, b = thought_content_words(left), thought_content_words(right)
    if len(a) < 3 or len(b) < 3:
        return False
    return len(a & b) / min(len(a), len(b)) >= 0.5


def colliding_chapter_names(
    names: list[str], other_names: list[str]
) -> list[str]:
    mine = {n.lower() for n in names if n.lower() not in _GENERIC_CHAPTERS}
    theirs = {n.lower() for n in other_names if n.lower() not in _GENERIC_CHAPTERS}
    return sorted(mine & theirs)


def the_one_word_chapter_count(names: list[str]) -> int:
    return sum(1 for n in names if _THE_ONE_WORD.match(n))

_ERRORS: list[str] = []


def _fail(msg: str) -> None:
    _ERRORS.append(msg)
    print(f"ERROR   {msg}")


def _warn(msg: str) -> None:
    print(f"warning {msg}")


def _ok(msg: str) -> None:
    print(f"ok      {msg}")


def _narration_of(fixture: dict) -> str:
    parts = [fixture.get("hook", "")]
    for level in fixture.get("levels", []):
        parts.extend(level.get("beats", []))
    return " ".join(p for p in parts if p)


def _ngrams(text: str, n: int = 4) -> set[tuple[str, ...]]:
    words = re.findall(r"[a-z']+", text.lower())
    return {tuple(words[i : i + n]) for i in range(len(words) - n + 1)}


def _sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"[.!?]+", text) if s.strip()]


def _other_story_fixtures(self_path: Path) -> list[tuple[Path, dict]]:
    out: list[tuple[Path, dict]] = []
    for other in sorted((ROOT / "fixtures").glob("*.json")):
        if other.resolve() == self_path.resolve():
            continue
        if other.name.endswith("image_jobs.json") or other.name.endswith(
            "_short.json"
        ):
            continue
        try:
            data = json.loads(other.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue
        if not isinstance(data, dict) or "levels" not in data:
            continue
        out.append((other, data))
    return out


def _lint_unique_engine(fixture: dict, fixture_path: Path) -> None:
    """Fail a new title that borrowed another cut's cards, payoff, or open."""
    names = chapter_names(fixture)
    thought = (fixture.get("the_thought") or "").strip()
    hook = (fixture.get("hook") or "").strip()
    mode = mode_for_slug(fixture_path.stem)
    if hook_is_month_year_stamp(hook):
        _fail(
            "story engine: cold open starts with 'Month Year.' — that stamp "
            "is used up. Open on a sourced object, room, line, or reversal "
            "this title owns"
        )
    ones = the_one_word_chapter_count(names)
    if ones > 3:
        _fail(
            f"story engine: {ones} chapters are 'The <Noun>' posters "
            "(max 3). Invent cards this evidence owns (a place, a paper, "
            "a date), not a generic The Suit / The Rocket row"
        )
    for other_path, other in _other_story_fixtures(fixture_path):
        if mode_for_slug(other_path.stem) != mode:
            continue
        hits = colliding_chapter_names(names, chapter_names(other))
        if hits:
            _fail(
                f"story engine: chapter {hits[0]!r} already ships in "
                f"{other_path.name} — new title, new cards"
            )
        other_thought = (other.get("the_thought") or "").strip()
        if thought and other_thought and thoughts_too_close(thought, other_thought):
            _fail(
                f"story engine: the_thought is too close to {other_path.name} "
                f"({other_thought!r}) — answer this title in this story's words"
            )
        if thought and other_thought and thought.lower().rstrip(".") == other_thought.lower().rstrip("."):
            _fail(
                f"story engine: the_thought is identical to {other_path.name}"
            )


def main() -> None:
    if len(sys.argv) < 2:
        print("usage: lint_story.py <spec.json> [--short]", file=sys.stderr)
        sys.exit(2)
    spec = json.loads((ROOT / sys.argv[1]).read_text(encoding="utf-8"))
    short = "--short" in sys.argv[2:]
    parent_fixture: Path | None = None
    if short:
        if "short" not in spec:
            print("spec has no \"short\" block", file=sys.stderr)
            sys.exit(2)
        # The Short retells its own long video's opening, so overlap with the
        # parent fixture is expected and not a novelty failure.
        parent_fixture = (ROOT / spec["fixture"]).resolve()
        spec = {**spec, **spec["short"]}
    fixture_path = (ROOT / spec["fixture"]).resolve()
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    narration = _narration_of(fixture)
    lowered = narration.lower()

    # 1. NOVELTY vs every other fixture that has the levels structure.
    new_grams = _ngrams(narration)
    for other in sorted((ROOT / "fixtures").glob("*.json")):
        if other.resolve() in (fixture_path, parent_fixture) or other.name.endswith(
            "image_jobs.json"
        ):
            continue
        try:
            data = json.loads(other.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue
        if not isinstance(data, dict) or "levels" not in data:
            continue
        other_grams = _ngrams(_narration_of(data))
        if not new_grams or not other_grams:
            continue
        overlap = len(new_grams & other_grams) / len(new_grams)
        if overlap > 0.10:
            _fail(
                f"novelty: {overlap:.0%} of the narration's 4-grams also appear "
                f"in {other.name} — this is a recycled script, not a new story"
            )
        elif overlap > 0.03:
            _warn(f"novelty: {overlap:.0%} 4-gram overlap with {other.name}")
        else:
            _ok(f"novelty vs {other.name}: {overlap:.1%} overlap")

    # 2. MOTIFS banned by shipped videos' "Do not copy" sections.
    # Skip this cut's own page (and the parent long-cut page for a Short) —
    # those quotes exist so the *next* title cannot steal them.
    def _page_slug(title: str) -> str:
        return re.sub(r"[^a-z0-9]+", "-", (title or "").lower()).strip("-")

    own_pages = {_page_slug(fixture.get("title") or ""), fixture_path.stem}
    if fixture_path.stem.endswith("_short"):
        own_pages.add(fixture_path.stem[: -len("_short")])
    if parent_fixture is not None:
        own_pages.add(parent_fixture.stem)
        try:
            parent_data = json.loads(parent_fixture.read_text(encoding="utf-8"))
            own_pages.add(_page_slug(parent_data.get("title") or ""))
        except (json.JSONDecodeError, UnicodeDecodeError, OSError):
            pass
    own_pages.discard("")
    banned: list[tuple[str, str]] = []  # (phrase, source page)
    motif_dirs = [ROOT / "docs" / "videos", ROOT / "docs" / "business"]
    for page in sorted(p for d in motif_dirs if d.is_dir() for p in d.glob("*.md")):
        if page.stem in own_pages:
            continue
        text = page.read_text(encoding="utf-8")
        m = re.search(r"## Do not copy.*?(?=\n## |\Z)", text, flags=re.S)
        if not m:
            continue
        for phrase in re.findall(r"[“\"]([^”\"]{4,120})[”\"]", m.group(0)):
            banned.append((phrase.strip().lower(), page.name))
    hits = [(p, src) for p, src in banned if p and p in lowered]
    for phrase, src in hits:
        _fail(f"motif: {phrase!r} is on the do-not-copy list of {src}")
    if not hits:
            _ok(
                f"no banned motifs ({len(banned)} phrases checked from "
                "docs/videos/ and docs/business/)"
            )

    # 2b. Unique story engine — new channel titles only.
    if spec.get("engine") == "channel" and not short:
        if fixture_path.stem in _UNIQUENESS_GRANDFATHERED:
            _ok(f"story engine: {fixture_path.stem} is grandfathered")
        else:
            _lint_unique_engine(fixture, fixture_path)

    # 3. NARRATOR: third person, no lecture numbering.
    for pat, why in [
        (r"\bI (will|am|count|see|know)\b", "narrator-'I' — narrator is third person"),
        (r"\b(fake|reason|rule|lesson|mistake) number (one|two|three|\d)\b",
         "numbered-lecture phrasing"),
        (r"\bnumber (one|two|three|four|five)[.:]", "numbered-lecture phrasing"),
    ]:
        m = re.search(pat, narration)
        if m:
            _fail(f"voice: {why} (found {m.group(0)!r})")

    # 4. SPOKEN English.
    sents = _sentences(narration)
    tiny = [s for s in sents if len(s.split()) <= 3]
    if sents and len(tiny) / len(sents) > 0.30:
        _fail(
            f"register: {len(tiny)}/{len(sents)} sentences are <=3 words — "
            "telegram fragments read as a robot; punches are seasoning, not the meal"
        )
    else:
        _ok(f"{len(tiny)}/{len(sents)} short-punch sentences")
    if not re.search(r"\w+'(s|t|re|ll|ve|d)\b", narration):
        _warn("no contractions anywhere — this reads as written, not spoken English")

    # 4b. EXPLAIN-LIKE-FIVE — the thought must be sayable by a child.
    thought = (fixture.get("the_thought") or "").strip()
    if not thought:
        if is_business(spec.get("channel_mode")):
            _fail(
                "explain-like-five: add the_thought — one sentence that answers "
                "the business mystery"
            )
        else:
            _fail(
                "explain-like-five: add the_thought — one sentence a child could "
                "repeat, naming what the hero believed"
            )
    else:
        needle = re.sub(r"\s+", " ", thought.lower()).rstrip(".")
        hay = re.sub(r"\s+", " ", lowered)
        if needle not in hay:
            _fail(
                f"explain-like-five: the_thought must appear in the narration "
                f"as written: {thought!r}"
            )
        elif len(thought.split()) > config_for(spec.get("channel_mode")).title_payoff_max_words:
            limit = config_for(spec.get("channel_mode")).title_payoff_max_words
            _fail(
                f"explain-like-five: the_thought is {len(thought.split())} words "
                f"(max {limit}) — a viewer has to be able to repeat it"
            )
        else:
            _ok(f"the_thought: {thought!r}")

    # 5. STRUCTURE.
    if not fixture.get("hook", "").strip():
        _fail("structure: fixture has no hook (cold-open line)")
    levels = fixture.get("levels", [])
    if short:
        # A traffic Short: 25-45s of speech, open loop, spoken CTA at the end.
        words = len(re.findall(r"\S+", narration))
        short_cfg = config_for(spec.get("channel_mode"))
        secs = words / (short_cfg.narration_wpm / 60)
        lo_s, hi_s = short_cfg.short_word_min, short_cfg.short_word_max
        if not lo_s <= words <= hi_s:
            _fail(
                f"short length: {words} words (~{secs:.0f}s at "
                f"{short_cfg.narration_wpm} wpm) — write {lo_s}-{hi_s} words"
            )
        else:
            _ok(f"short length: {words} words (~{secs:.0f}s)")
        last_beat = (levels[-1].get("beats") or [""])[-1].lower() if levels else ""
        new_cta = "watch the full video" in last_beat and "description" in last_beat
        old_cta = bool(
            re.search(
                r"full story|whole story|on (this|the) channel|link below",
                last_beat,
            )
        )
        grandfathered = fixture_path.stem in {
            "einstein-religion_short",
            "einstein-zionism_short",
        }
        if not new_cta and not (grandfathered and old_cta):
            _fail(
                "short CTA: the last beat must be "
                "'Watch the full video. The link is in the description.'"
            )
        if fixture.get("include_level_titles", True):
            _fail("short structure: set include_level_titles: false (no cards)")
    elif fixture.get("title_style") == "chapter":
        ch_cfg = config_for(spec.get("channel_mode"))
        if not ch_cfg.chapter_count_min <= len(levels) <= ch_cfg.chapter_count_max:
            _fail(
                f"structure: {len(levels)} chapters — use "
                f"{ch_cfg.chapter_count_min}-{ch_cfg.chapter_count_max}"
            )
        if fixture.get("speak_title_cards", True):
            _fail("structure: chapter cards must be silent (speak_title_cards: false)")
        for level in levels:
            name = level.get("name", "")
            if len(name.split()) > 4:
                _fail(f"structure: chapter name {name!r} is not poster-like (<=4 words)")
    for level in levels:
        if not level.get("beats"):
            _fail(f"structure: chapter {level.get('name')!r} has no beats")

    # Channel engine (What They Really Think): extra spoken-doc checks.
    # Older fixtures omit "engine" and must keep passing.
    words = len(re.findall(r"\S+", narration))
    if spec.get("engine") == "channel":
        hook = (fixture.get("hook") or "").strip()
        hook_words = hook.split()
        head = " ".join(hook_words[:40]).lower()
        if re.search(r"\b(was|were)\s+born\b", head):
            _fail(
                "cold open: biography dump ('was born') — start with the "
                "title's mystery, not a birth"
            )
        if is_business(spec.get("channel_mode")) and re.search(
            r"\b(was|were)\s+founded\b", head
        ):
            _fail(
                "cold open: company-history dump ('was founded') — start with "
                "the business contradiction"
            )
        for opener in (
            "this video will",
            "in this video",
            "today we are going to",
            "let us begin by",
        ):
            if opener in head:
                _fail(f"cold open: lecture opener {opener!r}")
        if not short and fixture_path.stem not in _LENGTH_GRANDFATHERED:
            lo, hi = (
                config_for(spec.get("channel_mode")).narration_word_min,
                config_for(spec.get("channel_mode")).narration_word_max,
            )
            if words < lo:
                _warn(f"length: {words} words (channel target {lo}-{hi})")
            elif words > hi:
                _warn(f"length: {words} words (channel target {lo}-{hi})")
            else:
                _ok(f"length: {words} words")
        lower_all = narration.lower()
        for phrase in (
            "furthermore",
            "consequently",
            "nevertheless",
            "it is important to note",
            "from a geopolitical perspective",
            "it can therefore be concluded",
            "during this particular period",
        ):
            if phrase in lower_all:
                _warn(f"register: written-essay phrase {phrase!r}")
        if "but that wasn't the whole story" in lower_all:
            _warn("stock transition 'But that wasn't the whole story' — vary it")
        spelled = SPELLED_YEAR.search(narration)
        if spelled and fixture_path.stem not in _WORD_YEAR_GRANDFATHERED:
            _fail(
                "years: write calendar years as digits (1995), not "
                f"{spelled.group(0)!r}. Captions show the digits; Kokoro "
                "speaks the year"
            )
        clock = production_clock_hit(narration)
        if clock:
            _fail(
                "clock: research through today, but do not say the production "
                f"date in the VO (found {clock!r}). Date events with months "
                "and years (August 2026), not 'today is' / 'as of today' / "
                "'this morning'"
            )
        advice = advisor_voice_hit(narration)
        if advice:
            _fail(
                "advisor: this channel does not give medical, legal, or "
                "investment advice "
                f"(found {advice!r})"
            )
        from channel.originality_policy import (
            GENERIC_AI_PHRASES,
            STOCK_ENDINGS,
            STOCK_HOOK_OPENERS,
            STOCK_TRANSITIONS,
        )

        for phrase in GENERIC_AI_PHRASES:
            if phrase in lower_all:
                _fail(f"register: generic AI phrase {phrase!r} — write spoken English")
        hook_head = hook.lower()[:400]
        for phrase in STOCK_HOOK_OPENERS:
            if phrase in hook_head:
                _fail(
                    f"hook: stock opener {phrase!r} — start from this title's "
                    "strongest sourced moment"
                )
        for phrase in STOCK_TRANSITIONS:
            if phrase in lower_all:
                _fail(
                    f"transition: stock line {phrase!r} — write one this event owns"
                )
        tail = narration.lower()[-800:]
        for phrase in STOCK_ENDINGS:
            if phrase in tail:
                _fail(
                    f"ending: stock closer {phrase!r} — pick a different "
                    "ending strategy"
                )
        if not short:
            from channel.originality import originality_report_for_slug, regenerate_targets

            orig = originality_report_for_slug(fixture_path.stem)
            if orig.flags and not orig.ready_for_images:
                for flag in orig.flags:
                    _fail(f"originality: {flag}")
                targets = regenerate_targets(orig)
                if targets:
                    _fail("originality: regenerate " + ", ".join(targets))
            elif orig.originality_score < 80:
                _fail(
                    f"originality: score {orig.originality_score} < 80 "
                    "against recent videos"
                )
    elif not short:
        _ok(f"{words} words")

    if _ERRORS:
        print(f"\n{len(_ERRORS)} error(s). Rewrite the story before touching stills.")
        sys.exit(1)
    print("\nStory passes.")


if __name__ == "__main__":
    main()
