"""Calendar years stay digits on screen; TTS speaks them as years."""

from __future__ import annotations

from adapters.voice.years import SPELLED_YEAR, speak_years, year_to_words


def test_year_to_words_american_spoken():
    assert year_to_words(1900) == "nineteen hundred"
    assert year_to_words(1908) == "nineteen oh eight"
    assert year_to_words(1911) == "nineteen eleven"
    assert year_to_words(1929) == "nineteen twenty-nine"
    assert year_to_words(1983) == "nineteen eighty-three"
    assert year_to_words(1995) == "nineteen ninety-five"
    assert year_to_words(2000) == "two thousand"
    assert year_to_words(2008) == "two thousand eight"
    assert year_to_words(2011) == "twenty eleven"
    assert year_to_words(2025) == "twenty twenty-five"


def test_speak_years_leaves_captions_source_as_digits():
    written = "In 1995, Steve Jobs sat for a camera."
    assert "1995" in written
    spoken = speak_years(written)
    assert spoken == "In nineteen ninety-five, Steve Jobs sat for a camera."
    assert "1995" not in spoken


def test_speak_years_skips_short_numbers_and_versions():
    text = "Windows 95 shipped after a hundred and fifty million dollars."
    assert speak_years(text) == text
    assert speak_years("Windows 1.0 and 2100 stay put.") == (
        "Windows 1.0 and 2100 stay put."
    )


def test_speak_years_expands_several_in_one_line():
    assert speak_years("From 1983 to 2011 he kept the insult.") == (
        "From nineteen eighty-three to twenty eleven he kept the insult."
    )


def test_spelled_year_lint_catches_old_style():
    assert SPELLED_YEAR.search("In nineteen ninety-five, Steve Jobs sat")
    assert SPELLED_YEAR.search("Go back to nineteen eighty-three.")
    assert SPELLED_YEAR.search("May, twenty eleven.")
    assert SPELLED_YEAR.search("two thousand eight")
    assert not SPELLED_YEAR.search("In 1995, Steve Jobs sat")
    assert not SPELLED_YEAR.search("for the next eighteen months")
    assert not SPELLED_YEAR.search("twenty people in the room")
    assert not SPELLED_YEAR.search("two thousand soldiers")
