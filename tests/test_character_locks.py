from pathlib import Path

from channel.character_locks import (
    REGISTRY_PATH,
    SHEETS_DIR,
    apply_character_locks,
    entry_for,
    load_registry,
    reference_image_paths,
)
from channel.schema import Character, Scene, ScenePurpose, TitleAnalysis, VideoProject

ROOT = Path(__file__).resolve().parent.parent


def test_registry_sheets_are_hashed_and_present():
    people = load_registry()
    assert people, f"missing registry at {REGISTRY_PATH}"
    assert SHEETS_DIR.is_dir()
    for entry in people:
        for key in ("sheet", "photo"):
            rel = str(entry.get(key) or "")
            if key == "sheet":
                assert rel, entry
            if not rel:
                continue
            name = Path(rel).name
            stem = Path(rel).stem
            assert rel.startswith("channel/character_sheets/"), entry
            assert set(stem) <= set("0123456789abcdef"), f"{key} filename must be hashed hex, got {name}"
            assert "elon" not in name.lower() and "sam" not in name.lower()
            assert "beast" not in name.lower() and "jimmy" not in name.lower()
            assert "trump" not in name.lower() and "donald" not in name.lower()
            assert (ROOT / rel).is_file(), rel
        assert "recognizable cartoon of the real person" in str(entry.get("visual_lock") or "")


def test_lookup_and_apply_by_historical_name():
    elon = entry_for("Elon Musk")
    sam = entry_for("Sam Altman")
    jimmy = entry_for("Jimmy Donaldson")
    beast = entry_for("MrBeast")
    trump = entry_for("Donald Trump")
    assert elon and sam
    assert jimmy and beast and jimmy["id"] == beast["id"]
    assert trump and trump["id"] == "donald-trump"
    assert "comb-over" in trump["visual_lock"]
    project = VideoProject(
        title="t",
        slug="t",
        analysis=TitleAnalysis(
            title="t",
            subject="Elon Musk",
            target="Sam Altman",
            core_question="q",
        ),
        characters={
            "elon": Character(id="elon", display_name="x", historical_name="Elon Musk", visual_lock="stale"),
            "sam": Character(id="sam", display_name="y", historical_name="Sam Altman", visual_lock="stale"),
            "extra": Character(id="extra", display_name="z", historical_name="Someone Else", visual_lock="keep"),
        },
    )
    applied = apply_character_locks(project)
    assert set(applied) == {"elon", "sam"}
    assert project.characters["elon"].visual_lock == elon["visual_lock"]
    assert project.characters["sam"].visual_lock == sam["visual_lock"]
    assert project.characters["extra"].visual_lock == "keep"


def test_reference_paths_photo_then_sheet_and_skip_empty():
    elon = entry_for("Elon Musk")
    sam = entry_for("Sam Altman")
    project = VideoProject(
        title="t",
        slug="t",
        analysis=TitleAnalysis(title="t", subject="Elon Musk", target="Sam Altman", core_question="q"),
        characters={
            "elon": Character(id="elon", display_name="x", historical_name="Elon Musk", is_subject=True),
            "sam": Character(id="sam", display_name="y", historical_name="Sam Altman"),
        },
    )
    hero = Scene(
        scene_id="a",
        narration="n",
        purpose=ScenePurpose.context,
        action="points",
        characters=["elon"],
        who="hero",
    )
    both = Scene(
        scene_id="b",
        narration="n",
        purpose=ScenePurpose.context,
        action="two men",
        characters=["elon", "sam"],
        who="hero",
    )
    empty = Scene(
        scene_id="c",
        narration="n",
        purpose=ScenePurpose.context,
        action="empty loft",
        characters=["elon"],
        who="empty",
    )
    hero_refs = reference_image_paths(project, hero)
    assert hero_refs[0] == elon["photo"]
    assert hero_refs[1] == elon["sheet"]
    both_refs = reference_image_paths(project, both)
    assert both_refs == [elon["photo"], elon["sheet"], sam["photo"], sam["sheet"]]
    assert reference_image_paths(project, empty) == []
    thumb = reference_image_paths(project)
    assert thumb == [elon["photo"], elon["sheet"]]
