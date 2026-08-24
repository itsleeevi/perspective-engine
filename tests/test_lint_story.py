"""Story-lint helpers that future titles must keep passing."""

from pathlib import Path

from scripts.lint_story import (
    advisor_voice_hit,
    colliding_chapter_names,
    generic_ai_hit,
    hook_is_month_year_stamp,
    long_spoken_number_hit,
    production_clock_hit,
    the_one_word_chapter_count,
    thoughts_too_close,
)


def test_production_clock_rejects_today_is_date():
    assert production_clock_hit("Today is August 22, 2026. The factory is open.")
    assert production_clock_hit("As of today, the courts have not given him the lab.")
    assert production_clock_hit("So what does he really think about AI, today, August 22, 2026.")
    assert production_clock_hit("The parents punched in this morning.")
    assert production_clock_hit("and ten days ago that warehouse shipped another version")


def test_generic_ai_register_is_rejected():
    assert generic_ai_hit("It is important to note that the alliance was temporary.")
    assert generic_ai_hit("Throughout history men have asked this.")
    assert generic_ai_hit("But Stalin had another problem.") is None


def test_advisor_voice_rejects_channel_as_doctor_or_broker():
    assert advisor_voice_hit("You should invest in this fund before the crash.")
    assert advisor_voice_hit("See a doctor if the cough lasts.")
    assert advisor_voice_hit("As your lawyer I would file tomorrow.")
    assert advisor_voice_hit("He thought people are animals who learned to be kind.") is None
    assert advisor_voice_hit("Survival of the fittest was not his phrase for conscience.") is None


def test_long_spoken_numbers_are_rejected():
    assert long_spoken_number_hit("Tesla printed 158,359,009,867 dollars.") == "158,359,009,867"
    assert long_spoken_number_hit("The option covers 303960630 shares.") == "303960630"
    assert long_spoken_number_hit("about 158 billion dollars in 2025") is None
    assert long_spoken_number_hit("a typical worker is about 63 thousand") is None


def test_production_clock_allows_event_dates():
    assert production_clock_hit("In August 2026 he told SpaceX staff they were the parents.") is None
    assert production_clock_hit("On August 14, 2026 he said AI would become 99 percent.") is None
    assert production_clock_hit("Today the factory is open.") is None


def test_hook_month_year_stamp_is_the_recycled_open():
    assert hook_is_month_year_stamp("February 2026. Jeff Bezos posted one picture.")
    assert hook_is_month_year_stamp("October 2014. A hall at MIT.")
    assert not hook_is_month_year_stamp(
        "A black phone on a desk shows one animal and no words."
    )


def test_chapter_names_cannot_reuse_a_shipped_card():
    hits = colliding_chapter_names(
        ["The Pad", "Pad 39A"],
        ["The Suit", "The Rocket", "The Pad"],
    )
    assert hits == ["the pad"]


def test_the_one_word_chapter_cap():
    names = ["The Picture", "The Pad", "The Suit", "The Rocket", "The Moon"]
    assert the_one_word_chapter_count(names) == 5
    mixed = ["Pad 39A", "Slow Is Smooth", "The Boom", "Jacklyn", "Skip Steps"]
    assert the_one_word_chapter_count(mixed) == 1


def test_thoughts_too_close_catches_a_relabeled_payoff():
    assert thoughts_too_close(
        "He thinks we die unless he builds the machine first.",
        "He thinks we die unless he builds the machine first",
    )
    assert thoughts_too_close(
        "He thinks we die unless he builds the machine first.",
        "He thinks people die unless he builds that machine first.",
    )
    assert not thoughts_too_close(
        "He thinks we die unless he builds the machine first.",
        "He thinks Elon is the hare, and skipping steps does not make you faster.",
    )


def test_new_title_fails_reused_cards_and_month_stamp():
    from scripts import lint_story as ls

    ls._ERRORS.clear()
    fixture = {
        "the_thought": "He thinks we die unless he builds the machine first.",
        "hook": "February 2026. Someone posted a picture on a phone.",
        "levels": [
            {"name": "The Suit", "beats": ["a"]},
            {"name": "The Rocket", "beats": ["b"]},
            {"name": "The Lab", "beats": ["c"]},
            {"name": "The Factory", "beats": ["d"]},
            {"name": "The Moon", "beats": ["e"]},
        ],
    }
    ls._lint_unique_engine(fixture, Path("fixtures/brand-new-title.json"))
    blob = " ".join(ls._ERRORS).lower()
    assert "month year" in blob or "cold open" in blob
    assert "the suit" in blob or "the rocket" in blob or "the lab" in blob
    assert "too close" in blob or "identical" in blob
    ls._ERRORS.clear()
