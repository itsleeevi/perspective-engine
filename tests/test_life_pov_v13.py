"""v13 life POV master setting, blocks, and Section 17A checks."""

from __future__ import annotations

from pathlib import Path

from channel.life_pov_blocks import (
    ABSENCE,
    FINISHING,
    MASTER_TITLE,
    SKIN_LOCK_PREFIX,
    STYLE_OBJECT,
    STYLE_PEOPLE,
)
from channel.validate_scene_batch import normalize, validate_scene_batch, SceneLedgerRow
from channel.wealth_prompts import MASTER
from channel.wealth_title import analyze_wealth_title

ROOT = Path(__file__).resolve().parent.parent
EXAMPLE_SOURCE = """
[00:00] You wait beside the closed rehearsal-room door.
[00:05] Your teacher opens the door.
[00:09] The microphone is already waiting inside.
[00:14] You step into the room.
"""


def test_master_is_full_v13_document():
    assert MASTER_TITLE in MASTER
    assert "END OF MASTER PROMPT v13" in MASTER
    assert "Section 17A" in MASTER
    assert STYLE_PEOPLE in MASTER
    assert "validate_scene_batch.py" in MASTER
    text = (ROOT / "channel" / "wealth_pov_master_v13.txt").read_text(encoding="utf-8")
    assert text.startswith(MASTER_TITLE)
    assert "WHAT CHANGED IN v13" in text


def test_section12_example_batch_passes_17a():
    source = normalize(EXAMPLE_SOURCE, strip_cues=True)
    s1 = "You wait beside the closed rehearsal-room door."
    s2 = "Your teacher opens the door."
    s3 = "The microphone is already waiting inside."
    i1 = source.find(s1)
    i2 = source.find(s2)
    i3 = source.find(s3)
    assert i1 == 0
    ledger = [
        SceneLedgerRow("00:00", i1, i2),
        SceneLedgerRow("00:05", i2, i3),
        SceneLedgerRow("00:09", i3, i3 + len(s3)),
    ]
    p1 = (
        f"[00:00] {STYLE_PEOPLE} Medium-wide view of an original fictional "
        "sixteen-year-old aspiring singer waiting beside a closed muted-blue "
        "rehearsal-room door. "
        f"{SKIN_LOCK_PREFIX}face, ear, neck and hands"
        "; no peach, pink, tan, beige, cream, off-white, gray, blush or lighting tint. "
        f"{FINISHING}"
    )
    p2 = (
        f"[00:05] {STYLE_PEOPLE} An original fictional middle-aged female teacher "
        "stands inside the open muted-blue rehearsal-room door. "
        f"{ABSENCE} {FINISHING}"
    )
    p3 = (
        f"[00:09] {STYLE_OBJECT} Close object-only view of an unused black "
        f"microphone on a simple upright stand. {ABSENCE} {FINISHING}"
    )
    prompts = f"{p1}\n\n{p2}\n\n{p3}\n"
    placement = (
        '[00:00] IMAGE: A teenage singer waits beside a closed blue rehearsal-room door. '
        'SHOW FROM: "You wait beside the closed rehearsal-room" '
        'KEEP UNTIL: "wait beside the closed rehearsal-room door."\n\n'
        '[00:05] IMAGE: Her teacher holds the newly opened blue door from inside the room. '
        'SHOW FROM: "Your teacher opens the door." '
        'KEEP UNTIL: "Your teacher opens the door."\n\n'
        '[00:09] IMAGE: An unused black microphone waits inside the rehearsal room, with no people visible. '
        'SHOW FROM: "The microphone is already waiting inside." '
        'KEEP UNTIL: "The microphone is already waiting inside."\n'
    )
    report = validate_scene_batch(
        EXAMPLE_SOURCE,
        prompts,
        placement,
        ledger,
        strip_cues=True,
        final_batch=False,
        batch_size=3,
        banned={"Cristiano Ronaldo"},
    )
    failed = [c.name for c in report.checks if not c.ok]
    assert report.ok, failed


def test_inner_brackets_and_name_fail():
    source = "Hello there world now."
    body = (
        f"[S001] {STYLE_PEOPLE} A man named Cristiano Ronaldo waves. "
        f"{ABSENCE} {FINISHING}"
    )
    place = (
        '[S001] IMAGE: A wave. SHOW FROM: "Hello there world now." '
        'KEEP UNTIL: "Hello there world now."'
    )
    report = validate_scene_batch(
        source,
        body + "\n",
        place + "\n",
        [SceneLedgerRow("S001", 0, len(source))],
        final_batch=True,
        batch_size=1,
        banned={"Cristiano Ronaldo"},
    )
    names = {c.name: c.ok for c in report.checks}
    assert names["BANNED_IN_PROMPTS"] is False


def test_you_are_turning_point_title():
    a = analyze_wealth_title("POV: You Are Taylor Swift. The Tour Decision")
    assert a.category == "documented life"
    assert a.subject == "Taylor Swift"
    assert "Tour Decision" in a.target
