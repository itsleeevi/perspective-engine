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
3. NARRATOR  — third person only. Narrator-"I" ("I will count the fakes")
               and lecture numbering ("fake number one", "level two") are
               errors.
4. SPOKEN    — telegram-fragment share capped (short sentences are punches,
               not the default register); zero contractions is flagged as
               written-not-spoken English.
4b. EXPLAIN-LIKE-FIVE — fixture must have ``the_thought`` (≤22 words, a
               child could repeat it) and that sentence must appear in the VO.
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

ROOT = Path(__file__).resolve().parent.parent

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

    own_pages = {_page_slug(fixture.get("title") or "")}
    if parent_fixture is not None:
        try:
            parent_data = json.loads(parent_fixture.read_text(encoding="utf-8"))
            own_pages.add(_page_slug(parent_data.get("title") or ""))
        except (json.JSONDecodeError, UnicodeDecodeError, OSError):
            pass
    own_pages.discard("")
    banned: list[tuple[str, str]] = []  # (phrase, source page)
    for page in sorted((ROOT / "docs" / "videos").glob("*.md")):
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
        _ok(f"no banned motifs ({len(banned)} phrases checked from docs/videos/)")

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
        elif len(thought.split()) > 22:
            _fail(
                f"explain-like-five: the_thought is {len(thought.split())} words "
                "(max 22) — a child has to be able to say it"
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
        secs = words / (175 / 60)
        if not 60 <= words <= 135:
            _fail(
                f"short length: {words} words (~{secs:.0f}s at 175 wpm) — "
                "write 60-135 words so the Short lands in 25-45s"
            )
        else:
            _ok(f"short length: {words} words (~{secs:.0f}s)")
        last_beat = (levels[-1].get("beats") or [""])[-1].lower() if levels else ""
        if not re.search(r"full story|whole story|on (this|the) channel|link below",
                         last_beat):
            _fail(
                "short CTA: the last beat must send viewers to the long video "
                "('The full story is on this channel.')"
            )
        if fixture.get("include_level_titles", True):
            _fail("short structure: set include_level_titles: false (no cards)")
    elif fixture.get("title_style") == "chapter":
        if not 4 <= len(levels) <= 6:
            _fail(f"structure: {len(levels)} chapters — use 4-6")
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
        for opener in (
            "this video will",
            "in this video",
            "today we are going to",
            "let us begin by",
        ):
            if opener in head:
                _fail(f"cold open: lecture opener {opener!r}")
        if not short:
            if words < 650:
                _warn(f"length: {words} words (channel target 650-750)")
            elif words > 750:
                _warn(f"length: {words} words (channel target 650-750)")
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
    elif not short:
        _ok(f"{words} words")

    if _ERRORS:
        print(f"\n{len(_ERRORS)} error(s). Rewrite the story before touching stills.")
        sys.exit(1)
    print("\nStory passes.")


if __name__ == "__main__":
    main()
