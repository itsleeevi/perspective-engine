"""Quality bar extracted from the best-performing shipped cuts."""

from __future__ import annotations

from pathlib import Path

from channel.agent_prompts import BIBLES as WTRT_BIBLES
from channel.agent_prompts import SCENE_BREAKDOWN as WTRT_SCENES
from channel.agent_prompts import SHORTS as WTRT_SHORTS
from channel.agent_prompts import STORY_ARCHITECT as WTRT_STORY
from channel.business_prompts import BIBLES as BTB_BIBLES
from channel.business_prompts import SCENE_BREAKDOWN as BTB_SCENES
from channel.business_prompts import SHORTS as BTB_SHORTS
from channel.business_prompts import STORY_ARCHITECT as BTB_STORY
from channel.character_locks import entry_for
from channel.config import GLOBAL_VISUAL_STYLE
from channel.prompts import assemble_image_prompt
from channel.quality_bar import (
    QUALITY_BAR_DOC,
    STAGING_QUALITY,
    action_head,
    is_person_title,
    prompt_markers,
    repeated_action_heads,
    scene_quality_notes,
    stills_quality_notes,
    visual_lock_gaps,
    wallpaper_hits,
)
from channel.schema import (
    Character,
    Location,
    Scene,
    ScenePurpose,
    TitleAnalysis,
    VideoProject,
)
from channel.takeover_prompts import BIBLES as HTTO_BIBLES
from channel.takeover_prompts import SCENE_BREAKDOWN as HTTO_SCENES
from channel.takeover_prompts import SHORTS as HTTO_SHORTS
from channel.takeover_prompts import STORY_ARCHITECT as HTTO_STORY

ROOT = Path(__file__).resolve().parent.parent


def test_quality_bar_doc_exists():
    assert (ROOT / QUALITY_BAR_DOC).is_file()


def test_prompt_modules_carry_quality_markers():
    blobs = (
        WTRT_STORY,
        WTRT_BIBLES,
        WTRT_SCENES,
        WTRT_SHORTS,
        BTB_STORY,
        BTB_BIBLES,
        BTB_SCENES,
        BTB_SHORTS,
        HTTO_STORY,
        HTTO_BIBLES,
        HTTO_SCENES,
        HTTO_SHORTS,
    )
    joined = "\n".join(blobs)
    for marker in prompt_markers():
        assert marker in joined, marker
    for blob in (WTRT_STORY, BTB_STORY, HTTO_STORY):
        assert QUALITY_BAR_DOC in blob
        assert "kid map of 5-8 steps" in blob
    for blob in (WTRT_SCENES, BTB_SCENES, HTTO_SCENES):
        assert "oversized focal object" in blob.replace("\n", " ")
    for blob in (WTRT_BIBLES, BTB_BIBLES, HTTO_BIBLES):
        assert "Same cartoon person every time" in blob


def test_person_title_heuristic():
    assert is_person_title("What Elon Musk Really Thinks About Sam Altman")
    assert is_person_title("How Donald Trump Really Makes His Money")
    assert not is_person_title("How Costco Really Makes Money")
    assert not is_person_title("How Tesla Took Over the Electric Car Industry")


def test_wallpaper_and_repeated_heads():
    wall = "Clean business illustration of a filing table, a glass cabinet, same construction, no logos, no readable type."
    assert wallpaper_hits(wall)
    actions = [wall] * 20 + ["Shopper in a slate sweater slams a gold card at the door."]
    assert repeated_action_heads(actions)
    unique = [f"SET unique verb {i} huge object warm lamp" for i in range(40)]
    assert not repeated_action_heads(unique)


def test_stills_quality_notes_catch_wallpaper():
    actions = [
        "Clean business illustration of a filing table, same construction, no logos, no readable type."
    ] * 20
    errors, _warnings = stills_quality_notes(actions, ["empty"] * 20, title="How Costco Really Makes Money")
    assert errors


def test_visual_lock_recipe_and_trump_registry():
    trump = entry_for("Donald Trump")
    assert trump
    assert not visual_lock_gaps(trump["visual_lock"], historical_name="Donald Trump")
    gaps = visual_lock_gaps("a man in a room", historical_name="")
    assert gaps


def test_assembled_prompt_includes_staging_quality():
    project = VideoProject(
        title="What Elon Musk Really Thinks About Sam Altman",
        slug="elon-musk-sam-altman",
        analysis=TitleAnalysis(
            title="What Elon Musk Really Thinks About Sam Altman",
            subject="Elon Musk",
            target="Sam Altman",
            core_question="q",
        ),
        characters={
            "elon": Character(
                id="elon",
                display_name="x",
                historical_name="Elon Musk",
                is_subject=True,
                visual_lock=entry_for("Elon Musk")["visual_lock"],
            )
        },
        locations={"loft": Location(id="loft", description="glass loft, long table")},
        scenes=[
            Scene(
                scene_id="s1",
                narration="n",
                purpose=ScenePurpose.hook,
                action="rectangular-jaw man slams both palms on the long table.",
                characters=["elon"],
                location="loft",
                who="hero",
            )
        ],
    )
    prompt = assemble_image_prompt(project, project.scenes[0])
    assert GLOBAL_VISUAL_STYLE[:40] in prompt
    assert STAGING_QUALITY[:40] in prompt
    assert "oversized focal object" in prompt
    assert "Elon" not in prompt
    notes = scene_quality_notes(project)
    assert not any("wallpaper" in n for n in notes)
