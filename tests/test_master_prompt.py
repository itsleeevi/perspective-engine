"""Master prompt is the staged operator loop; DNA is per channel."""

from channel.agent_prompts import MASTER as THINK_MASTER
from channel.agent_prompts import NARRATION_WRITER as THINK_VO
from channel.business_prompts import MASTER as MONEY_MASTER
from channel.master_prompt import master_for
from channel.modes import ChannelMode
from channel.stage_prompts import master_prompt, stage_prompts_for
from channel.takeover_prompts import MASTER as TAKEOVER_MASTER


def test_each_channel_exports_master():
    assert stage_prompts_for("what_they_really_think").MASTER is THINK_MASTER
    assert stage_prompts_for("behind_the_business").MASTER is MONEY_MASTER
    assert stage_prompts_for("how_they_took_over").MASTER is TAKEOVER_MASTER
    assert master_prompt("what_they_really_think") == THINK_MASTER
    assert master_for(ChannelMode.how_they_took_over) == TAKEOVER_MASTER


def test_master_shares_operator_loop():
    for blob in (THINK_MASTER, MONEY_MASTER, TAKEOVER_MASTER):
        assert "800–2500" in blob
        assert "WAIT_AUDIO" in blob
        assert "ingest-audio" in blob
        assert "Google Flow" in blob
        assert 'Reply "next"' in blob
        assert "batches of 20" in blob
        assert "not Midjourney" in blob
        assert "doodle" in blob.lower()
        assert "stick figure" in blob.lower()
        assert "2nd-person" in blob


def test_channel_dna_does_not_cross_contaminate():
    assert "What They Really Think" in THINK_MASTER
    assert "behind_the_business" not in THINK_MASTER
    assert "How They Really Make Money" in MONEY_MASTER
    assert "How They Took Over" in TAKEOVER_MASTER
    assert "Pass --channel behind_the_business" in MONEY_MASTER
    assert "Pass --channel how_they_took_over" in TAKEOVER_MASTER


def test_think_vo_forbids_second_person_explainer():
    assert 'Never "you"' in THINK_VO
    assert "800–2500" in THINK_VO
