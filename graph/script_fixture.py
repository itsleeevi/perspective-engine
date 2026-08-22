"""
Load and expand script fixtures for stick-figure level POV videos.

Fixtures supply a fixed title + ordered levels with narration beats so test
runs (and demos) can skip LLM script generation while still exercising the
rest of the pipeline.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

from graph import style

_LEVEL_WORDS = (
    "One",
    "Two",
    "Three",
    "Four",
    "Five",
    "Six",
    "Seven",
    "Eight",
    "Nine",
    "Ten",
    "Eleven",
    "Twelve",
)

TITLE_PREFIX = "[TITLE]"

_FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures"

SPECIAL_FORCES_TITLE = "Your Life as Every Rank in Special Forces"
DEFAULT_SPECIAL_FORCES_FIXTURE = _FIXTURES_DIR / "your_life_special_forces.json"

CIA_TITLE = "Your Life As Every CIA Black Ops Rank"
DEFAULT_CIA_FIXTURE = _FIXTURES_DIR / "cia_black_ops.json"

_DEMO_FIXTURES = {
    SPECIAL_FORCES_TITLE.lower(): DEFAULT_SPECIAL_FORCES_FIXTURE,
    CIA_TITLE.lower(): DEFAULT_CIA_FIXTURE,
}


def is_title_beat(text: str) -> bool:
    return text.strip().upper().startswith(TITLE_PREFIX)


def title_card_lines(title_beat: str) -> tuple[str, str]:
    """
    Parse ``[TITLE] Level One: The Recruit`` into (line1, line2).

    Returns (full text, "") if no colon separator is found.
    """
    raw = title_beat.strip()
    if raw.upper().startswith(TITLE_PREFIX):
        raw = raw[len(TITLE_PREFIX) :].strip()
    if ":" in raw:
        left, right = raw.split(":", 1)
        return f"{left.strip()}:", right.strip()
    return raw, ""


def title_card_narration(title_beat: str) -> str:
    """
    Spoken form of a title card: ``[TITLE] Level One: The Recruit`` becomes
    ``Level One. The Recruit.``

    The level name is narrated over its card so a transition is a beat in the
    story rather than dead air.
    """
    line1, line2 = title_card_lines(title_beat)
    left = line1.rstrip(":").strip()
    if not line2:
        return f"{left}."
    return f"{left}. {line2.rstrip('.')}."


def narration_duration_seconds(text: str, words_per_minute: float = 150.0) -> float:
    """Estimate on-screen duration from narration word count."""
    words = len(text.split())
    if words == 0:
        return 2.5
    seconds = words / words_per_minute * 60.0
    return max(3.0, min(seconds, 45.0))


# Measured wpm of the production voice (ElevenLabs Liam, adapters.voice
# .elevenlabs) from a real render: 66 words -> 23.82s. An earlier 136.0 taken
# from edge-tts left every chunk 22% shorter than the target window, because
# the paid voice reads noticeably faster than the free one.
#
# Chunk sizing below is built on this so the estimate driving chunking is
# close to what will actually be spoken; the voice adapters separately measure
# the *real* per-word timing of the synthesised audio and use that (not this
# estimate) to set each shot's exact on-screen duration, so an off wpm here
# only shifts which words land on which image, never the audio/video sync.
# Override with NARRATION_WPM in the environment when the production voice
# is not ElevenLabs Liam. Kokoro ``am_liam`` at speed 1.0 measures ~205 wpm
# on long-form prose (short samples look slower because pauses dominate).
def _narration_wpm() -> float:
    raw = os.environ.get("NARRATION_WPM")
    if raw:
        return float(raw)
    return 166.0


NARRATION_WPM = _narration_wpm()

# Target on-screen time per image: a cut every ~3-4 seconds.
#
# Chunking is sentence- and clause-aware, NOT fixed-size word grouping. An
# earlier version sliced every beat into equal word groups on the theory that
# the reference format cuts once per auto-caption line; measuring a real
# render disproved it. Auto-generated YouTube caption lines do break
# mid-phrase, but the *picture* in those videos does not — it changes on
# sentence and clause boundaries, where the narrator actually pauses.
#
# The difference is audible. Measuring the rendered sample against speech
# onsets detected in its own audio: cuts that landed on a sentence boundary
# were 9-76 ms from the narration (imperceptible), while cuts that landed
# mid-phrase ("There's a form on the CIA | website.") were 700-960 ms from
# the nearest pause — the picture changing in the middle of a breath, which
# reads as the whole video being out of sync even though the timing maths
# was exact.
# The window has to be wide enough to pair two short consecutive sentences
# ("You apply online like everyone else. There's a form on the CIA website.")
# into one shot. Capping it near the target instead forces one image per
# sentence, which for this format's clipped narration is barely slower than
# the old fixed-word chunking it replaced.
CHUNK_MIN_SECONDS = 2.5
CHUNK_MAX_SECONDS = 5.5
CHUNK_TARGET_SECONDS = 4.0

# Sentence end: terminal punctuation followed by whitespace.
_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")
# Clause end: comma/semicolon/colon/dash followed by whitespace. Requiring the
# whitespace is what keeps "9,000" and "3:00" intact — a thousands separator
# or a clock has no space after its punctuation, so it never splits here.
_CLAUSE_SPLIT = re.compile(r"(?<=[,;:—–])\s+")


def _estimate_seconds(text: str, wpm: float) -> float:
    return len(text.split()) / wpm * 60.0


def _split_by_word_count(text: str, target_words: int) -> list[str]:
    """
    Split text into consecutive pieces of about ``target_words`` words.

    Last-resort fallback for a single clause too long to fit one shot, where
    there is no punctuation left to break on.
    """
    words = text.split()
    if not words:
        return []
    if len(words) <= target_words:
        return [text]
    pieces = [
        " ".join(words[i : i + target_words])
        for i in range(0, len(words), target_words)
    ]
    # A remainder under half the target reads as a rushed, near-empty shot;
    # folding it into the previous piece is closer to the target on average.
    if len(pieces) > 1 and len(pieces[-1].split()) < target_words / 2:
        last = pieces.pop()
        pieces[-1] = f"{pieces[-1]} {last}"
    return pieces


def _atoms(text: str, wpm: float, max_seconds: float) -> list[str]:
    """
    Break text into the smallest units a cut is allowed to fall between.

    Sentences first; a sentence too long for one shot is broken at clause
    punctuation; a clause still too long is finally broken by word count.
    """
    units: list[str] = []
    for sentence in _SENTENCE_SPLIT.split(text):
        sentence = sentence.strip()
        if not sentence:
            continue
        if _estimate_seconds(sentence, wpm) <= max_seconds:
            units.append(sentence)
            continue
        for clause in _CLAUSE_SPLIT.split(sentence):
            clause = clause.strip()
            if not clause:
                continue
            if _estimate_seconds(clause, wpm) <= max_seconds:
                units.append(clause)
            else:
                units.extend(
                    _split_by_word_count(clause, max(1, round(max_seconds / 60 * wpm)))
                )
    return units


def split_beat_into_chunks(
    beat: str,
    wpm: float = NARRATION_WPM,
    min_seconds: float = CHUNK_MIN_SECONDS,
    max_seconds: float = CHUNK_MAX_SECONDS,
    target_seconds: float = CHUNK_TARGET_SECONDS,
) -> list[str]:
    """
    Split one narration paragraph into ~3-4 second speaking chunks that begin
    and end where the narrator pauses.

    Sentences (and, where a sentence is too long, clauses) are packed greedily
    up to ``max_seconds``, closing a chunk once it has reached
    ``target_seconds`` so shots stay near the intended pace instead of always
    running to the maximum. Because every boundary is a punctuation boundary,
    every picture cut lands in a real pause in the delivered audio.

    Durations here are only estimates deciding *which words share an image* —
    the voice adapters measure the real per-word timing of the synthesised
    audio and set each shot's exact on-screen length from that, so an
    over- or under-sized group here never causes audio/video drift.
    """
    text = re.sub(r"\s+", " ", beat).strip()
    if not text:
        return []

    chunks: list[str] = []
    current: list[str] = []
    current_seconds = 0.0
    for unit in _atoms(text, wpm, max_seconds):
        unit_seconds = _estimate_seconds(unit, wpm)
        if current and current_seconds + unit_seconds > max_seconds:
            chunks.append(" ".join(current))
            current, current_seconds = [unit], unit_seconds
        else:
            current.append(unit)
            current_seconds += unit_seconds
        if current_seconds >= target_seconds:
            chunks.append(" ".join(current))
            current, current_seconds = [], 0.0
    if current:
        chunks.append(" ".join(current))

    # A trailing scrap ("Welcome to the CIA.") gets its own image for well
    # under a second otherwise; fold it back unless that busts the maximum.
    if len(chunks) > 1 and _estimate_seconds(chunks[-1], wpm) < min_seconds / 2:
        merged = f"{chunks[-2]} {chunks[-1]}"
        if _estimate_seconds(merged, wpm) <= max_seconds * 1.25:
            chunks = chunks[:-2] + [merged]
    return chunks


def load_fixture(path: str | Path) -> dict:
    """Load and validate a script fixture JSON file."""
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"Script fixture not found: {p}")
    data = json.loads(p.read_text(encoding="utf-8"))
    if "levels" not in data or not isinstance(data["levels"], list) or not data["levels"]:
        raise ValueError(f"Script fixture must contain a non-empty 'levels' list: {p}")
    return data


def fixture_to_beats(data: dict, include_hook: bool = True) -> list[str]:
    """
    Expand fixture levels into script beats.

    An optional top-level ``hook`` string is spoken first, before any title
    card — the cold open that decides whether a viewer keeps watching past the
    first five seconds. Set ``include_hook=False`` to drop it and start
    directly on Level One's title card, matching reference videos that open
    straight on the first level instead of a cold open.

    Each level becomes a ``[TITLE] Level N: Name`` beat followed by its
    narration paragraphs (second-person VO lines). Set
    ``include_level_titles`` to false on the fixture to skip the cards and
    play as a continuous scene.
    """
    beats: list[str] = []
    hook = str(data.get("hook", "")).strip()
    if hook and include_hook:
        beats.append(hook)
    include_titles = bool(data.get("include_level_titles", True))
    for i, level in enumerate(data["levels"]):
        name = str(level.get("name", f"Level {i + 1}")).strip()
        word = _LEVEL_WORDS[i] if i < len(_LEVEL_WORDS) else str(i + 1)
        if include_titles:
            beats.append(f"{TITLE_PREFIX} Level {word}: {name}")
        for para in level.get("beats", []):
            text = str(para).strip()
            if not text:
                continue
            beats.append(text)
    if not beats:
        raise ValueError("Fixture produced an empty beat list.")
    return beats


def resolve_fixture_path(topic: str, script_fixture_path: str = "") -> str:
    """
    Return the fixture path to use, if any.

    Explicit ``script_fixture_path`` wins. Otherwise, auto-select a demo
    fixture when the topic matches its title exactly.
    """
    if script_fixture_path.strip():
        return script_fixture_path.strip()
    path = _DEMO_FIXTURES.get(topic.strip().lower())
    if path is not None and path.is_file():
        return str(path)
    return ""


def _pick_visual_focus(beat: str) -> str:
    """
    Pick the most drawable moment from a narration beat.

    Long second-person monologues confuse image models into portraits; prefer
    a concrete action/location sentence and rewrite "you" as the hero.
    """
    text = re.sub(r"\s+", " ", beat).strip()
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]
    if not sentences:
        return text

    place_words = (
        r"\b(office|garage|forest|base|hut|village|helicopter|rifle|airplane|swamp|"
        r"classroom|porch|tarmac|door|bus|field|warehouse|compound|school|well|ambush|"
        r"cemetery|funeral|barracks|desert|mountain|strip mall|parachute|rucksack|beret|"
        r"hospital|kitchen|porch)\b"
    )
    action_words = (
        r"\b(sign|lift|run|jump|fall|walk|train|raid|kick|shoot|drag|salute|bury|drink|"
        r"teach|carry|build|fly|shave|scream|march|quit|brief)\b"
    )

    def score(s: str) -> int:
        low = s.lower()
        pts = len(re.findall(place_words, low)) * 3
        pts += len(re.findall(action_words, low)) * 2
        if re.match(r"you'?re\s+\d+\s+years", low):
            pts -= 8
        if low.startswith("you're still") or low.startswith("then you"):
            pts -= 1
        return pts

    ranked = sorted(sentences, key=score, reverse=True)
    focus = ranked[0]

    if score(focus) <= 0 and len(sentences) > 1:
        focus = " ".join(sentences[:2])
    return focus


_SECOND_PERSON_SUBSTITUTIONS = (
    (r"\byou're\b", "he is"),
    (r"\byou are\b", "he is"),
    (r"\byou've\b", "he has"),
    (r"\byou have\b", "he has"),
    (r"\byou'll\b", "he will"),
    (r"\byou will\b", "he will"),
    (r"\byou'd\b", "he would"),
    (r"\byourself\b", "himself"),
    (r"\byours\b", "his"),
    (r"\byour\b", "his"),
    (r"\byou\b", "he"),
)

_IRREGULAR_VERBS = {
    "be": "is",
    "have": "has",
    "do": "does",
    "go": "goes",
    "don't": "does not",
}


def _conjugate(verb: str) -> str:
    """Third-person singular form of a bare present-tense verb."""
    lower = verb.lower()
    if lower in _IRREGULAR_VERBS:
        return _IRREGULAR_VERBS[lower]
    if lower.endswith(("s", "sh", "ch", "x", "z", "o")):
        return f"{verb}es"
    if lower.endswith("y") and len(lower) > 1 and lower[-2] not in "aeiou":
        return f"{verb[:-1]}ies"
    return f"{verb}s"


def to_third_person(text: str) -> str:
    """
    Rewrite second-person narration as a third-person description.

    Used when no LLM is available. Image models read "you" as an instruction to
    frame the viewer and return a camera-facing close-up, so the pronoun has to
    go even if the result is a little stiff; the LLM path in
    ``LLMAdapter.visualize_beats`` produces better copy when it is available.
    """
    result = text
    for pattern, replacement in _SECOND_PERSON_SUBSTITUTIONS:
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)

    # "he sign the papers" -> "he signs the papers". Only a verb directly after
    # the pronoun is adjusted; anything more needs a real parser.
    def fix(match: re.Match) -> str:
        pronoun, verb = match.group(1), match.group(2)
        if verb.lower() in ("is", "has", "was", "will", "would", "can", "could"):
            return match.group(0)
        return f"{pronoun} {_conjugate(verb)}"

    return re.sub(r"\b(he)\s+([a-z]+)\b", fix, result)


def scene_prompt_from_beat(
    beat: str, style_descriptor: str = "", career_stage: str = ""
) -> str:
    """
    Build an image prompt for the most drawable moment in a narration beat.

    Fallback for runs without an LLM: picks the most concrete sentence and
    strips the second person. The visual style and hero identity come from
    ``graph.style``; this function only decides *what* to draw.
    """
    focus = _pick_visual_focus(beat)
    if len(focus) > 240:
        focus = focus[:239].rsplit(" ", 1)[0] + "…"
    return style.scene_prompt(
        to_third_person(focus), style_descriptor, career_stage=career_stage
    )
