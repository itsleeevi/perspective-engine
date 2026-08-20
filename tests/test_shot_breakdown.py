"""
Tests for shot_breakdown's beat-chunking and index-aligned scene mapping.

Requirements exercised here:
- Narration beats are split into ~3-4 second chunks (script_fixture) so the
  picture changes several times per paragraph (AGENTS.md: cover control flow,
  not just imports).
- Chunking is sentence- and clause-aware: every chunk boundary falls where
  the narrator pauses, which is what keeps picture cuts in sync with the
  narration. Cuts measured mid-phrase in a real render sat up to a second
  from the nearest pause and read as badly out of sync.
- Splitting never drops or duplicates narration words.
- A title beat always produces exactly one shot, never chunked.
- shot_breakdown maps each LLM-visualized scene back onto the correct chunk
  by index, even when the LLM/local rewriter returns a different scene count
  than the number of chunks for a beat (regression coverage for the indexed-
  mapping fix — a positional zip would silently misalign every later shot).
- Character-free shot types are prompted without the hero description.
"""

from __future__ import annotations

import pytest

from adapters.llm.mock import MockLLMAdapter
from graph import style
from graph.nodes.shot_breakdown import _expand_script, _shots_from_units, shot_breakdown
from graph.script_fixture import (
    CHUNK_MAX_SECONDS,
    CHUNK_MIN_SECONDS,
    NARRATION_WPM,
    split_beat_into_chunks,
)
from graph.state import CharacterRefs, PipelineState, ShotMode


class TestSplitBeatIntoChunks:
    def test_short_beat_stays_one_chunk(self):
        chunks = split_beat_into_chunks("You sign the papers at a desk.")
        assert len(chunks) == 1

    def test_long_beat_splits_into_multiple_chunks(self):
        beat = (
            "You sign the papers at an office in a strip mall. The recruiter "
            "shakes your hand. He smiles like you just won something. You do "
            "not know what you won yet."
        )
        chunks = split_beat_into_chunks(beat)
        assert len(chunks) > 1

    def test_chunks_mostly_land_in_target_window(self):
        beat = (
            "They send you to Camp Perry, Virginia. The locals call it the "
            "farm. It's 9,000 acres of woods, swamps, and training facilities "
            "surrounded by fences topped with razor wire and armed guards at "
            "every gate."
        )
        chunks = split_beat_into_chunks(beat)
        seconds = [len(c.split()) / NARRATION_WPM * 60.0 for c in chunks]
        # Every chunk but possibly the last should sit inside the window;
        # a trailing remainder is allowed to be short.
        for s in seconds[:-1]:
            assert CHUNK_MIN_SECONDS - 1.0 <= s <= CHUNK_MAX_SECONDS + 1.0

    def test_no_words_lost_or_duplicated(self):
        """
        Regression test: an earlier bug in the word-count splitter used
        ``pieces.pop()`` inside the same expression that indexed into the
        (now-shorter) list, silently dropping a whole piece.
        """
        beat = (
            "Small unit tactics, close quarters combat, explosives and "
            "demolitions, advanced weapons training, high altitude parachute "
            "operations, free falling from 30,000 ft, combat diving, sear "
            "survival, evasion, resistance, and escape, where they confine "
            "you in a box for days to teach you what captivity feels like "
            "before it happens for real."
        )
        chunks = split_beat_into_chunks(beat)
        assert " ".join(chunks).split() == beat.split()

    def test_empty_beat_produces_no_chunks(self):
        assert split_beat_into_chunks("") == []
        assert split_beat_into_chunks("   ") == []

    def test_chunks_end_where_the_narrator_pauses(self):
        """
        Every cut must land on punctuation the narrator actually pauses on.

        Measured on a real render, cuts that fell on a sentence boundary were
        9-76 ms from the narration while cuts that fell mid-phrase were
        700-960 ms from the nearest pause — the single largest source of the
        picture looking out of sync.
        """
        beat = (
            "You apply online like everyone else. There's a form on the CIA "
            "website. You fill in your name, your education, your work "
            "history. You click submit and wait."
        )
        chunks = split_beat_into_chunks(beat)
        assert len(chunks) > 1
        for chunk in chunks:
            assert chunk.rstrip().endswith((".", "!", "?", ",", ";", ":"))

    def test_long_clauseless_sentence_still_splits(self):
        """
        A sentence too long for one shot with no internal punctuation has no
        pause to cut on; it must still be split rather than held for 15
        seconds on one image.
        """
        beat = " ".join(["word"] * 60) + "."
        chunks = split_beat_into_chunks(beat)
        assert len(chunks) > 1
        assert " ".join(chunks).split() == beat.split()

    def test_numbers_are_not_split_at_their_commas(self):
        """
        "9,000" and "3:00" contain clause punctuation but no pause. The
        splitter requires whitespace after the punctuation, so they stay whole.
        """
        beat = "It's 9,000 acres of woods and the gate opens at 3:00 sharp."
        for chunk in split_beat_into_chunks(beat):
            assert not chunk.startswith(("000", "00"))


class TestExpandScript:
    def test_title_beat_is_never_chunked(self):
        units = _expand_script(["[TITLE] Level One: The Applicant"])
        assert len(units) == 1
        assert units[0][0] == "title"

    def test_narration_beat_expands_to_multiple_units(self):
        long_beat = (
            "You apply online like everyone else. There's a form on the CIA "
            "website. You fill in your name, your education, your work "
            "history. You click submit and wait."
        )
        units = _expand_script([long_beat])
        assert all(kind == "chunk" for kind, _ in units)
        assert len(units) > 1

    def test_mixed_script_preserves_order(self):
        script = [
            "[TITLE] Level One: The Applicant",
            "You apply online like everyone else. You wait.",
            "[TITLE] Level Two: The Trainee",
        ]
        units = _expand_script(script)
        assert units[0][0] == "title"
        assert units[-1][0] == "title"
        assert any(kind == "chunk" for kind, _ in units[1:-1])


class TestShotsFromUnits:
    def test_scene_descriptions_land_on_the_right_chunk(self):
        """
        A ``scenes`` map missing an index (e.g. the LLM dropped that item)
        must not shift later scenes onto the wrong chunk — each description
        is keyed by its own unit index, resolved via ``dict.get`` rather than
        a positional zip.
        """
        units = [
            ("chunk", "First chunk text."),
            ("chunk", "Second chunk text."),
            ("chunk", "Third chunk text."),
        ]
        # Index 1 is deliberately missing, simulating a dropped LLM item.
        scenes = {0: "scene for first", 2: "scene for third"}

        shots = _shots_from_units(units, "bald head", scenes, {})

        assert len(shots) == 3
        assert "scene for first" in shots[0].prompt
        # The missing index falls back to the local rewriter instead of
        # silently reusing a neighboring scene.
        assert "scene for" not in shots[1].prompt
        assert "scene for third" in shots[2].prompt

    def test_character_free_shots_omit_the_hero_description(self):
        """
        A prompt for an object-only shot must not carry the hero description.
        Appending it makes the image model add a person to a frame that was
        specified as having none — the stronger the model, the more literally
        it does so.
        """
        units = [("chunk", "A price tag."), ("chunk", "He signs the form.")]
        scenes = {0: "A price tag filling the frame.", 1: "A man signs a form."}

        shots = _shots_from_units(
            units, "oversized bald round head", scenes, {0: False, 1: True}
        )

        assert "oversized bald round head" not in shots[0].prompt
        assert "oversized bald round head" in shots[1].prompt

    def test_unknown_shot_index_keeps_the_hero(self):
        """An absent entry must default to including the hero, not dropping it."""
        units = [("chunk", "He waits.")]
        shots = _shots_from_units(units, "bald head", {0: "A man waits."}, {})
        assert "bald head" in shots[0].prompt

    def test_character_free_shots_forbid_people_explicitly(self):
        """
        Omitting the hero is not the same as asking for an empty frame. Left
        implicit, the image model supplies its own person.
        """
        units = [("chunk", "A price tag.")]
        shots = _shots_from_units(
            units, "bald head", {0: "A price tag filling the frame."}, {0: False}
        )
        assert "NO PEOPLE IN THIS FRAME" in shots[0].prompt

    def test_career_stage_advances_across_title_cards(self):
        """
        The hero's career-stage note must escalate as the shot list crosses
        level title cards, and stay put within a level — otherwise two
        consecutive shots in the same scene could describe him at different
        points in his career.
        """
        units = [
            ("title", "[TITLE] Level One: The Recruit"),
            ("chunk", "He starts his first day."),
            ("title", "[TITLE] Level Eight: The Director"),
            ("chunk", "He runs the agency now."),
        ]
        shots = _shots_from_units(
            units, "bald head", {1: "A man at a desk.", 3: "A man in an office."}, {}
        )
        early_prompt = shots[1].prompt
        late_prompt = shots[3].prompt
        assert "CAREER STAGE" in early_prompt
        assert "CAREER STAGE" in late_prompt
        assert early_prompt != late_prompt
        assert style.HERO_CAREER_STAGES[0] in early_prompt
        assert style.HERO_CAREER_STAGES[-1] in late_prompt

    def test_career_stage_present_even_without_a_preceding_title_card(self):
        """
        Narration ahead of any title card (should not normally happen, but
        must not crash or index negatively) still gets a valid stage.
        """
        units = [("chunk", "He waits before the first level card.")]
        shots = _shots_from_units(units, "bald head", {0: "A man waits."}, {})
        assert "CAREER STAGE" in shots[0].prompt

    def test_career_stage_can_be_disabled(self):
        units = [
            ("title", "[TITLE] Level One: The Arrest"),
            ("chunk", "He sits in a cell."),
        ]
        shots = _shots_from_units(
            units,
            "bald head",
            {1: "A man in an orange jumpsuit sits on a bunk."},
            {},
            hero_career_progression=False,
        )
        assert "CAREER STAGE" not in shots[1].prompt
        assert "bald head" in shots[1].prompt


class TestCareerStageNote:
    def test_bucketing_covers_first_and_last_stage(self):
        assert style.career_stage_note(0, 8) == style.HERO_CAREER_STAGES[0]
        assert style.career_stage_note(7, 8) == style.HERO_CAREER_STAGES[-1]

    def test_single_level_script_gets_the_earliest_stage(self):
        assert style.career_stage_note(0, 1) == style.HERO_CAREER_STAGES[0]

    def test_stage_is_monotonic_across_levels(self):
        """
        A script's stage index must never decrease as the level index rises —
        the whole point is that he does not get visually demoted mid-video.
        """
        total = 12
        indices = [
            style.HERO_CAREER_STAGES.index(style.career_stage_note(i, total))
            for i in range(total)
        ]
        assert indices == sorted(indices)


class TestMentionsPerson:
    """
    The storyboard is told never to mention a person in a character-free shot
    and does it anyway. ``mentions_person`` is the backstop that keeps such a
    description from being rendered with no hero *and* no people-ban, which
    is what put an off-style stranger in the frame.
    """

    @pytest.mark.parametrize(
        "description",
        [
            "Handwritten notes on the interviewer's notepad read 'Arrested?'.",
            "A pen hovers over the page in his hand.",
            "A crowd of identical silhouettes with one highlighted.",
            "A young man signs papers at a desk.",
        ],
    )
    def test_detects_implied_people(self, description):
        assert style.mentions_person(description)

    @pytest.mark.parametrize(
        "description",
        [
            "A notepad on a desk beside a coffee ring stain.",
            "A dusty laptop vent filling the frame.",
            "A locked steel door under a single bulb.",
        ],
    )
    def test_passes_genuinely_empty_scenes(self, description):
        assert not style.mentions_person(description)

    @pytest.mark.parametrize(
        "description",
        [
            "A digital clock face showing '22:00', suspended in black.",
            "The hour hand and minute hand of a wall clock at a steep angle.",
            "A scratched watch face on an empty bedside table.",
            "Two framed photographs turned face-down on a windowsill.",
            "The worn arms of an empty chair in a waiting room.",
        ],
    )
    def test_object_compounds_are_not_people(self, description):
        """
        These read as person words out of context and are not. Getting this
        wrong is not a near miss: "a digital clock face showing '22:00'" was
        flagged on the word *face*, so the hero was appended to a frame the
        storyboard had explicitly emptied, and the render came back as a man
        on a couch at home in the middle of a job interview.
        """
        assert not style.mentions_person(description)

    def test_person_wins_over_a_character_free_label(self):
        """
        A description that implies a person must get the hero back even when
        the storyboard labelled the shot character-free — otherwise the
        person in frame is nobody in particular.
        """
        units = [("chunk", "He is asked about his record.")]
        scenes = {0: "The interviewer's notepad, a pen hovering over it."}

        shots = _shots_from_units(
            units,
            "bald head",
            scenes,
            {0: style.mentions_person(scenes[0])},
        )

        assert "bald head" in shots[0].prompt
        assert "NO PEOPLE IN THIS FRAME" not in shots[0].prompt


@pytest.mark.asyncio
class TestShotBreakdownIndexedMapping:
    async def test_one_shot_per_chunk_plus_title(self):
        script = [
            "[TITLE] Level One: The Applicant",
            "You apply online like everyone else. There's a form on the CIA "
            "website. You fill in your name, your education, your work "
            "history. You click submit and wait.",
        ]
        state = PipelineState(
            script=script,
            character_refs=CharacterRefs(
                sheet_image_urls=["file:///ref.png"], style_descriptor="bald head"
            ),
        )
        result = await shot_breakdown(state, MockLLMAdapter())
        shots = result["shot_list"]

        title_shots = [s for s in shots if s.is_title_card]
        chunk_shots = [s for s in shots if not s.is_title_card]
        assert len(title_shots) == 1
        assert len(chunk_shots) == len(split_beat_into_chunks(script[1]))
        assert all(s.mode == ShotMode.static_pan for s in shots)

    async def test_max_shots_cap_applies_after_chunking(self):
        script = [
            "You apply online like everyone else. There's a form on the CIA "
            "website. You fill in your name, your education, your work "
            "history. You click submit and wait.",
        ]
        state = PipelineState(
            script=script,
            max_shots=2,
            character_refs=CharacterRefs(
                sheet_image_urls=["file:///ref.png"], style_descriptor="bald head"
            ),
        )
        result = await shot_breakdown(state, MockLLMAdapter())
        assert len(result["shot_list"]) == 2

    async def test_empty_script_raises(self):
        state = PipelineState(
            script=[],
            character_refs=CharacterRefs(
                sheet_image_urls=["file:///ref.png"], style_descriptor="bald head"
            ),
        )
        with pytest.raises(ValueError):
            await shot_breakdown(state, MockLLMAdapter())
