"""Quiet Wealth (wealth_pov) — must not leak into documentary channels."""

from __future__ import annotations

import pytest

from channel.config import (
    BEHIND_THE_BUSINESS,
    CHANNEL,
    HOW_THEY_TOOK_OVER,
    WEALTH_POV,
    WEALTH_POV_VISUAL_STYLE,
    config_for,
    kokoro_speed_for,
)
from channel.generate import start_job
from channel.locks import KOKORO_SPEED_MAX, KOKORO_SPEED_MIN
from channel.modes import ChannelMode, parse_mode
from channel.stage_prompts import stage_prompts_for
from channel.title import analyze_title
from channel.wealth_title import analyze_wealth_title, looks_like_wealth_pov


def test_wealth_config_is_a_fourth_channel():
    cfg = config_for("wealth_pov")
    assert cfg is WEALTH_POV
    assert cfg.name == "Quiet Wealth"
    assert cfg.target_duration_seconds == 1800
    assert cfg.min_duration_seconds == 1680
    assert cfg.max_duration_seconds == 1920
    assert cfg.narration_word_min == 4500
    assert cfg.narration_word_max == 4800
    assert cfg.min_scene_duration == 8.0
    assert cfg.max_scene_duration == 9.0
    assert cfg.visual_change_target_seconds == 8.5
    assert cfg.chapter_count_min == 6
    assert cfg.chapter_count_max == 6
    assert cfg.kokoro_speed == 1.15
    assert cfg.kokoro_speed >= KOKORO_SPEED_MIN
    assert cfg.kokoro_speed <= KOKORO_SPEED_MAX
    assert cfg.visual_style == WEALTH_POV_VISUAL_STYLE
    assert "stick-figure" not in cfg.visual_style.lower()
    assert "doodle" not in cfg.visual_style.lower()
    assert CHANNEL.visual_style != cfg.visual_style
    assert BEHIND_THE_BUSINESS.visual_style != cfg.visual_style
    assert HOW_THEY_TOOK_OVER.visual_style != cfg.visual_style
    assert cfg.videos_index == "docs/wealth/README.md"
    assert cfg.playbook == "docs/wealth-pov.md"
    assert kokoro_speed_for("pov-you-stopped-trying", cfg) == 1.15


def test_parse_mode_includes_wealth():
    assert parse_mode("wealth_pov") is ChannelMode.wealth_pov
    assert parse_mode("quiet_wealth") is ChannelMode.wealth_pov
    assert parse_mode("wpov") is ChannelMode.wealth_pov
    assert parse_mode("longform_wealth_pov") is ChannelMode.wealth_pov
    assert parse_mode("htto") is ChannelMode.how_they_took_over
    assert parse_mode("btb") is ChannelMode.behind_the_business
    assert parse_mode("wtrt") is ChannelMode.what_they_really_think


def test_pov_title_parses_choice_not_a_company():
    a = analyze_title(
        "POV: You Stopped Trying to Look Successful",
        channel_mode="wealth_pov",
    )
    assert a.channel_mode is ChannelMode.wealth_pov
    assert a.subject_status.value == "not_a_person"
    assert a.target_kind == "wealth_pov"
    assert "stopped trying to look successful" in a.subject.lower()
    assert "you" in a.core_question.lower()
    assert a.company == ""
    assert a.verb is None


def test_friends_misread_pattern():
    a = analyze_wealth_title(
        "POV: You Built Wealth Quietly. Your Friends Read It All Wrong"
    )
    assert a.channel_mode is ChannelMode.wealth_pov
    assert "built wealth quietly" in a.subject.lower()
    assert "friends" in a.target.lower()


def test_everyone_thinks_pattern():
    a = analyze_wealth_title(
        "POV: Everyone Thinks You're Broke, but You're Building a Cushion"
    )
    assert "broke" in a.core_question.lower()
    assert "cushion" in a.core_question.lower()


def test_looks_like_wealth_pov():
    assert looks_like_wealth_pov("POV: You Turned Down the Raise Everyone Else Wanted")
    assert not looks_like_wealth_pov("What Einstein Really Thought About God")
    assert not looks_like_wealth_pov("How Visa Really Makes Money")
    assert not looks_like_wealth_pov("How Nvidia Took Over AI")


def test_documentary_titles_rejected_in_wealth_mode():
    with pytest.raises(ValueError, match="what_they_really_think"):
        analyze_title(
            "What Einstein Really Thought About God",
            channel_mode="wealth_pov",
        )
    with pytest.raises(ValueError, match="behind_the_business"):
        analyze_title(
            "How Visa Really Makes Money",
            channel_mode="wealth_pov",
        )
    with pytest.raises(ValueError, match="how_they_took_over"):
        analyze_title(
            "How Nvidia Took Over AI",
            channel_mode="wealth_pov",
        )


def test_pov_title_without_mode_hints_wealth():
    with pytest.raises(ValueError, match="wealth_pov"):
        analyze_title("POV: You Stopped Trying to Look Successful")


def test_prompts_are_the_v5_master():
    prompts = stage_prompts_for("wealth_pov")
    assert "LONG-FORM ILLUSTRATED WEALTH POV MASTER PROMPT v5" in prompts.MASTER
    assert prompts.MASTER.startswith("You are the Quiet Wealth engine")
    assert "4,500" in prompts.NARRATION_WRITER
    assert "second person" in prompts.NARRATION_WRITER.lower()
    assert "NOT stick-figure" in prompts.BIBLES


def test_wealth_smoke_job(tmp_path):
    manifest = start_job(
        title="POV: You Stopped Trying to Look Successful",
        channel="wealth_pov",
        smoke_test=True,
        artifacts_root=tmp_path,
        job_id="wealth-smoke__test__aaa",
    )
    assert manifest.channel_mode == "wealth_pov"
    assert manifest.prompt_module == "channel.wealth_prompts"
    project = (tmp_path / "wealth-smoke__test__aaa" / "project.json").read_text(
        encoding="utf-8"
    )
    assert '"channel_mode": "wealth_pov"' in project
    assert "lunch tin" in project
