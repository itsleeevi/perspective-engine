"""What They Really Think channel engine — title-in, no person hardcoded."""

from __future__ import annotations

from pathlib import Path

import pytest

from channel.compile import chunk_list, compile_project, fixture_dict
from channel.config import CHANNEL, GLOBAL_VISUAL_STYLE
from channel.factcheck import factcheck
from channel.prompts import assemble_image_prompt
from channel.qa import mechanical_qa, visual_qa
from channel.schema import (
    Character,
    Chapter,
    Claim,
    EvidenceKind,
    Location,
    ResearchPack,
    Scene,
    ScenePurpose,
    SourceRef,
    StoryPlan,
    SubjectStatus,
    TitleAnalysis,
    VideoProject,
)
from channel.slug import slugify
from channel.title import analyze_title


EXAMPLE_TITLES = [
    "What Stalin Really Thought About Hitler",
    "What Hitler Really Thought About Americans",
    "What Einstein Really Thought About Religion",
    "What Steve Jobs Really Thought About Bill Gates",
    "What Xi Jinping Really Thinks About America",
    "What Churchill Really Thought About Stalin",
    "What Nietzsche Really Thought About Christianity",
]


class TestTitleAnalyzer:
    def test_all_channel_examples_parse(self):
        for title in EXAMPLE_TITLES:
            analysis = analyze_title(title)
            assert analysis.subject
            assert analysis.target
            assert analysis.core_question
            assert "unknown until researched" in analysis.relationship_type

    def test_thinks_means_living(self):
        a = analyze_title("What Xi Jinping Really Thinks About America")
        assert a.subject == "Xi Jinping"
        assert a.target == "America"
        assert a.verb == "Thinks"
        assert a.subject_status == SubjectStatus.living

    def test_thought_does_not_assume_the_answer(self):
        a = analyze_title("What Einstein Really Thought About Religion")
        assert a.subject == "Einstein"
        assert a.target == "Religion"
        assert a.verb == "Thought"
        assert a.time_period == "unknown until researched"

    def test_rejects_off_pattern(self):
        with pytest.raises(ValueError):
            analyze_title("Einstein on Religion")


class TestSlug:
    def test_slug_from_title(self):
        assert slugify("What Einstein Really Thought About Religion") == "einstein-religion"
        assert slugify("What Xi Jinping Really Thinks About America") == "xi-jinping-america"


class TestConfigHasNoPeople:
    def test_channel_config_has_no_example_people(self):
        text = Path("channel/config.py").read_text(encoding="utf-8").lower()
        for name in (
            "stalin",
            "hitler",
            "einstein",
            "nietzsche",
            "churchill",
            "jobs",
            "gates",
            "jinping",
        ):
            assert name not in text, f"{name} leaked into channel/config.py"


class TestFactcheck:
    def test_unsourced_quote_is_rejected(self):
        pack = ResearchPack(
            subject="A",
            target="B",
            claims=[
                Claim(
                    claim_id="claim_001",
                    claim='He said "hello"',
                    kind=EvidenceKind.said,
                    is_direct_quote=True,
                    quote="hello",
                    sources=[],
                )
            ],
            contradictions=["public vs private"],
        )
        report = factcheck(pack)
        assert not report.ok
        assert "claim_001" in report.rejected_claim_ids

    def test_sourced_quote_passes(self):
        pack = ResearchPack(
            subject="A",
            target="B",
            claims=[
                Claim(
                    claim_id="claim_001",
                    claim="A letter exists.",
                    kind=EvidenceKind.wrote,
                    is_direct_quote=True,
                    quote="I do not believe.",
                    sources=[SourceRef(title="Collected letters", kind="primary")],
                    confidence="high",
                )
            ],
            contradictions=["public vs private"],
        )
        assert factcheck(pack).ok


def _project() -> VideoProject:
    analysis = analyze_title("What Einstein Really Thought About Religion")
    payoff = "He did not believe in a personal God, but he was not done with wonder."
    hook = (
        f"{payoff} He spent years talking about God anyway. Why?"
    )
    body = (
        "He walked away from the God of his childhood. Then he kept using the word. "
        "Letters show what he meant, and what he refused to mean. "
        "There was a contradiction, and it was not a pose. "
        "The answer is in how he used the word God when he talked about the universe."
    )
    plan = StoryPlan(
        hook=hook,
        central_question=analysis.core_question,
        initial_assumption="People hear atheist.",
        first_reveal="He rejected a personal God.",
        major_contradiction="He kept talking about God.",
        turning_point="A letter spelled out the difference.",
        final_answer=payoff,
        title_payoff=payoff,
        next_video_bridge="What he thought about nationalism is another story. That story is next.",
        signature_prop="the letter",
        chapters=[
            Chapter(name="The Word", purpose=ScenePurpose.hook, narration=body),
            Chapter(name="The Break", purpose=ScenePurpose.context, narration=body),
            Chapter(name="The Letters", purpose=ScenePurpose.evidence, narration=body),
            Chapter(name="The Answer", purpose=ScenePurpose.resolution, narration=body + " " + payoff),
        ],
    )
    subject = Character(
        id="subject_adult",
        display_name="Subject",
        historical_name="Albert Einstein",
        face="simplified round face, simple eyes",
        hair="wild grey-white hair standing out",
        facial_hair="thick grey moustache",
        default_clothing="plain grey jacket, no tie",
        is_subject=True,
        visual_lock=(
            "CHARACTER subject_adult: older man, wild grey-white hair standing out, "
            "thick grey moustache, plain grey jacket, simple cartoon face, "
            "flat 2D vector, NOT photoreal"
        ),
    )
    loc = Location(
        id="study",
        description="simplified 1930s study, wooden desk, papers, muted brown palette",
    )
    return VideoProject(
        title=analysis.title,
        slug=slugify(analysis.title),
        analysis=analysis,
        research=ResearchPack(
            subject=analysis.subject,
            target=analysis.target,
            claims=[
                Claim(
                    claim_id="claim_001",
                    claim="A well-known letter distinguishes a personal God from wonder at the universe.",
                    kind=EvidenceKind.wrote,
                    sources=[SourceRef(title="Letter", kind="primary")],
                    confidence="high",
                    flags=[],
                )
            ],
            contradictions=["rejected personal God / kept using the word God"],
        ),
        story=plan,
        characters={subject.id: subject},
        locations={loc.id: loc},
        scenes=[],
    )


class TestPrompts:
    def test_assembled_prompt_has_global_style_not_historical_name(self):
        project = _project()
        scene = Scene(
            scene_id="scene_000",
            narration="He wrote a letter.",
            purpose=ScenePurpose.evidence,
            action="Older man at a wooden desk writes on a single sheet of paper.",
            composition="medium over-the-desk shot",
            characters=["subject_adult"],
            location="study",
            who="hero",
        )
        prompt = assemble_image_prompt(project, scene)
        assert GLOBAL_VISUAL_STYLE[:40] in prompt
        assert "Albert Einstein" not in prompt
        assert "Einstein" not in prompt
        assert "photorealistic" in prompt.lower()  # appears in the negation
        assert "NOT photorealistic".lower() in prompt.lower() or "Not photorealistic" in prompt


class TestVisualQa:
    def test_photoreal_action_is_flagged(self):
        project = _project()
        project.scenes = [
            Scene(
                scene_id="scene_000",
                narration="x",
                purpose=ScenePurpose.evidence,
                action="photorealistic portrait, DSLR photograph of skin texture",
                composition="close-up",
                characters=["subject_adult"],
                location="study",
                who="hero",
            )
        ]
        notes = visual_qa(project)
        assert any("photoreal" in n.lower() for n in notes)

    def test_name_in_visual_lock_is_flagged(self):
        project = _project()
        project.characters["subject_adult"].visual_lock = "Albert Einstein smiling"
        notes = visual_qa(project)
        assert any("historical_name" in n for n in notes)


class TestCompile:
    def test_compile_writes_fixture_spec_jobs(self, tmp_path: Path):
        project = _project()
        written = compile_project(project, stubs_ok=True, root=tmp_path)
        fixture = tmp_path / "fixtures" / "einstein-religion.json"
        spec = tmp_path / "fixtures" / "video_specs" / "einstein-religion.json"
        jobs = tmp_path / "fixtures" / "einstein-religion_v1_image_jobs.json"
        stills = tmp_path / "fixtures" / "einstein-religion_stills.py"
        assert fixture.is_file()
        assert spec.is_file()
        assert jobs.is_file()
        assert stills.is_file()
        data = fixture_dict(project)
        assert data["the_thought"] == project.story.title_payoff
        assert data["title_style"] == "chapter"
        spec_data = spec.read_text(encoding="utf-8")
        assert CHANNEL.name in spec_data
        assert '"engine": "channel"' in spec_data
        assert '"burn_captions": true' in spec_data
        assert '"kokoro_speed": 1.15' in spec_data
        assert '"kokoro_scene_pause": 0.28' in spec_data
        jobs_data = jobs.read_text(encoding="utf-8")
        assert "Albert Einstein" not in jobs_data
        assert "Einstein" not in jobs_data
        compile = stills.read_text(encoding="utf-8")
        compile_ok = compile  # syntax check
        compile_globals: dict = {}
        exec(compile_ok, compile_globals)
        assert "STILLS" in compile_globals
        chunks = chunk_list(project)
        assert len(compile_globals["STILLS"]) == len(chunks)
        assert written["jobs"].endswith("image_jobs.json")

    def test_compile_refuses_mismatched_scenes(self, tmp_path: Path):
        project = _project()
        with pytest.raises(ValueError, match="scene count"):
            compile_project(project, stubs_ok=False, root=tmp_path)


class TestMechanicalQa:
    def test_born_in_cold_open_hurts_hook(self):
        project = _project()
        assert project.story is not None
        project.story.hook = "Einstein was born in Ulm and went to school."
        scores = mechanical_qa(project)
        assert scores.hook < 8
        assert any("birth" in n.lower() or "born" in n.lower() for n in scores.notes)
