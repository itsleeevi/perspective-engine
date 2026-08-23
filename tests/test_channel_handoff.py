"""Guard the What They Really Think contract so other clones stay in sync.

A new agent in a fresh git checkout only sees tracked files. If a production
rule lives in chat or on one surface, the next environment will make a
different kind of video. These checks fail when the three agent surfaces
drift, or when a shipped video page is missing from the index.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

AGENT_SURFACES = (
    ROOT / "docs" / "custom-videos.md",
    ROOT / "AGENTS.md",
    ROOT / ".cursor" / "rules" / "custom-videos.mdc",
)

# If you change the product, update ALL three surfaces in the same commit.
REQUIRED_PHRASES = (
    "docs/custom-videos.md",
    "the_thought",
    "am_liam",
    "GenerateImage",
    "Watch the full video:",
    "synthetic-media",
    "4400–5500",
    "unique story engine",
    "originality_score",
    "ready_to_publish",
    "behind_the_business",
    "docs/behind-the-business.md",
    "3000–3750",
)


def test_agent_surfaces_exist():
    missing = [str(p.relative_to(ROOT)) for p in AGENT_SURFACES if not p.is_file()]
    assert not missing, f"missing agent surfaces: {missing}"


def test_agent_surfaces_share_production_invariants():
    for path in AGENT_SURFACES:
        text = path.read_text(encoding="utf-8")
        for phrase in REQUIRED_PHRASES:
            assert phrase in text, f"{path.relative_to(ROOT)} is missing {phrase!r}"


def test_playbook_names_the_shared_contract():
    playbook = (ROOT / "docs" / "custom-videos.md").read_text(encoding="utf-8")
    assert "Shared contract (other clones)" in playbook
    assert "tests/test_channel_handoff.py" in playbook


def test_business_playbook_exists():
    playbook = ROOT / "docs" / "behind-the-business.md"
    index = ROOT / "docs" / "business" / "README.md"
    assert playbook.is_file()
    assert index.is_file()
    text = playbook.read_text(encoding="utf-8")
    assert "behind_the_business" in text
    assert "unknown until researched" in text or "must **not** assume" in text


def test_videos_readme_lists_every_page():
    videos = ROOT / "docs" / "videos"
    readme = (videos / "README.md").read_text(encoding="utf-8")
    pages = sorted(p.name for p in videos.glob("*.md") if p.name != "README.md")
    missing = [name for name in pages if f"({name})" not in readme]
    assert not missing, (
        "docs/videos/README.md must link every shipped page so the next "
        f"clone sees the Do-not-copy list: {missing}"
    )
