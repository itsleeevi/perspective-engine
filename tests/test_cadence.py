"""Channel assemble cadence and per-title style / voice helpers."""

from datetime import datetime, timedelta, timezone

import pytest

from channel.cadence import (
    CADENCE_SECONDS,
    CadenceError,
    assert_cadence,
    record_assemble,
    slug_from_spec,
)
from channel.config import KOKORO_ROSTER, kokoro_voice_for, visual_accent_for
from channel.locks import SHIPPED_STYLE_LOCK
from graph.config import PUBLISH_CADENCE_SECONDS


def test_cadence_matches_graph_publish_cap():
    assert CADENCE_SECONDS == PUBLISH_CADENCE_SECONDS == 86_400


def test_same_slug_rebuild_is_allowed(tmp_path):
    now = datetime(2026, 8, 23, 9, 0, tzinfo=timezone.utc)
    record_assemble("darwin-human-nature", kind="long", root=tmp_path, now=now)
    assert_cadence(
        "darwin-human-nature",
        root=tmp_path,
        now=now + timedelta(minutes=10),
    )


def test_new_title_within_24h_is_blocked(tmp_path):
    now = datetime(2026, 8, 23, 9, 0, tzinfo=timezone.utc)
    record_assemble("darwin-human-nature", kind="long", root=tmp_path, now=now)
    with pytest.raises(CadenceError, match="--force"):
        assert_cadence(
            "next-title",
            root=tmp_path,
            now=now + timedelta(hours=2),
        )


def test_force_and_empty_log_allow(tmp_path):
    now = datetime(2026, 8, 23, 9, 0, tzinfo=timezone.utc)
    assert_cadence("first-title", root=tmp_path, now=now)
    record_assemble("first-title", kind="long", root=tmp_path, now=now)
    assert_cadence(
        "second-title",
        force=True,
        root=tmp_path,
        now=now + timedelta(hours=1),
    )
    assert_cadence(
        "second-title",
        root=tmp_path,
        now=now + timedelta(hours=25),
    )


def test_slug_from_spec_strips_short_suffix():
    spec = {
        "fixture": "fixtures/darwin-human-nature.json",
        "short": {"fixture": "fixtures/darwin-human-nature_short.json"},
    }
    assert slug_from_spec(spec) == "darwin-human-nature"
    assert slug_from_spec(spec, short=True) == "darwin-human-nature"


def test_shipped_slugs_keep_liam_and_no_accent():
    for slug in (
        "darwin-human-nature",
        "einstein-religion",
        "elon-musk-ai",
    ):
        assert slug in SHIPPED_STYLE_LOCK
        assert kokoro_voice_for(slug) == "am_liam"
        assert visual_accent_for(slug) == ""


def test_new_slug_gets_stable_roster_voice_and_accent():
    slug = "ada-lovelace-machines"
    voice = kokoro_voice_for(slug)
    accent = visual_accent_for(slug)
    assert voice in KOKORO_ROSTER
    assert accent
    assert kokoro_voice_for(slug) == voice
    assert visual_accent_for(slug) == accent
