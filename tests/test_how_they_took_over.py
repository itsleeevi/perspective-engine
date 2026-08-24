"""How They Took Over mode — must not leak into WTRT or Behind The Business."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from channel.compile import compile_project, spec_dict
from channel.config import (
    BEHIND_THE_BUSINESS,
    BEHIND_THE_BUSINESS_VISUAL_STYLE,
    CHANNEL,
    GLOBAL_VISUAL_STYLE,
    HOW_THEY_TOOK_OVER,
    HOW_THEY_TOOK_OVER_VISUAL_STYLE,
    config_for,
    kokoro_speed_for,
)
from channel.factcheck import factcheck
from channel.locks import KOKORO_SPEED_MIN
from channel.metadata import draft_metadata
from channel.modes import ChannelMode, parse_mode
from channel.originality import mode_for_slug, recent_slugs
from channel.prompts import assemble_image_prompt
from channel.schema import (
    Chapter,
    Claim,
    CompetitorNote,
    EvidenceKind,
    Flywheel,
    ResearchPack,
    Scene,
    ScenePurpose,
    SourceRef,
    StoryPlan,
    TakeoverContext,
    TurningPoint,
    VideoProject,
)
from channel.slug import slugify
from channel.takeover_title import analyze_takeover_title
from channel.takeover_titles import score_takeover_title, suggest_takeover_titles
from channel.takeover_visuals import TAKEOVER_VISUAL_TYPES
from channel.title import analyze_title


def test_htto_config_is_a_third_channel():
    cfg = config_for("how_they_took_over")
    assert cfg is HOW_THEY_TOOK_OVER
    assert cfg.name == "How They Took Over"
    assert cfg.target_duration_seconds == 1380
    assert cfg.min_duration_seconds == 1200
    assert cfg.max_duration_seconds == 1500
    assert cfg.narration_word_min == 4400
    assert cfg.narration_word_max == 5500
    assert cfg.kokoro_speed == 1.15
    assert cfg.kokoro_speed >= KOKORO_SPEED_MIN
    assert cfg.visual_style == HOW_THEY_TOOK_OVER_VISUAL_STYLE
    assert "How They Took Over" in cfg.visual_style
    assert "muted historical" not in cfg.visual_style
    assert "money flow" not in cfg.visual_style.lower()
    assert CHANNEL.visual_style != cfg.visual_style
    assert BEHIND_THE_BUSINESS.visual_style != cfg.visual_style
    assert cfg.visual_style != GLOBAL_VISUAL_STYLE
    assert cfg.visual_style != BEHIND_THE_BUSINESS_VISUAL_STYLE
    assert cfg.channel_handle == "@HowTheyTookOver"
    assert cfg.videos_index == "docs/takeover/README.md"
    assert cfg.playbook == "docs/how-they-took-over.md"
    assert kokoro_speed_for("acme-took-over-search", cfg) == 1.15


def test_parse_mode_three_channels():
    assert parse_mode("htto") is ChannelMode.how_they_took_over
    assert parse_mode("how_they_took_over") is ChannelMode.how_they_took_over
    assert parse_mode("takeover") is ChannelMode.how_they_took_over
    assert parse_mode("how_they_really_make_money") is ChannelMode.behind_the_business
    assert parse_mode("htrmm") is ChannelMode.behind_the_business
    assert parse_mode("btb") is ChannelMode.behind_the_business
    assert parse_mode("wtrt") is ChannelMode.what_they_really_think


def test_nvidia_title_does_not_assume_cuda():
    a = analyze_title(
        "How Nvidia Took Over AI",
        channel_mode="how_they_took_over",
    )
    blob = " ".join(
        [
            a.starting_position,
            a.dominant_position,
            a.possible_hidden_advantage,
            a.arena,
            a.core_question,
            *a.likely_turning_points,
            *a.potential_competitors,
        ]
    ).lower()
    assert a.subject == "Nvidia"
    assert a.company == "Nvidia"
    assert a.arena.lower() == "ai"
    assert a.verb is None
    assert a.channel_mode is ChannelMode.how_they_took_over
    assert a.target_kind == "takeover"
    assert "cuda" not in blob
    assert "unknown until researched" in a.possible_hidden_advantage
    assert "unknown until researched" in a.starting_position
    assert "how did nvidia take over ai" in a.core_question.lower()


def test_rolex_title_is_a_different_story_type():
    nvidia = analyze_title(
        "How Nvidia Took Over AI",
        channel_mode="how_they_took_over",
    )
    rolex = analyze_title(
        "How Rolex Became the Ultimate Status Symbol",
        channel_mode="how_they_took_over",
    )
    assert rolex.subject == "Rolex"
    assert rolex.channel_mode is ChannelMode.how_they_took_over
    assert "nvidia" not in rolex.core_question.lower()
    assert "cuda" not in rolex.core_question.lower()
    assert "ai" not in rolex.core_question.lower()
    assert nvidia.core_question != rolex.core_question
    assert "become the ultimate status symbol" in rolex.core_question.lower()


def test_money_title_rejected_in_takeover_mode():
    with pytest.raises(ValueError, match="behind_the_business"):
        analyze_title(
            "How Nvidia Really Makes Money",
            channel_mode="how_they_took_over",
        )


def test_wtrt_title_rejected_in_takeover_mode():
    with pytest.raises(ValueError, match="What They Really Think"):
        analyze_title(
            "What Einstein Really Thought About God",
            channel_mode="how_they_took_over",
        )


def test_takeover_title_without_mode_hints_htto():
    with pytest.raises(ValueError, match="how_they_took_over"):
        analyze_title("How Nvidia Took Over AI")


def test_visa_btb_and_einstein_wtrt_still_work():
    visa = analyze_title(
        "How Visa Really Makes Money",
        channel_mode="behind_the_business",
    )
    assert visa.channel_mode is ChannelMode.behind_the_business
    assert visa.company == "Visa"
    assert visa.company
    einstein = analyze_title("What Einstein Really Thought About God")
    assert einstein.channel_mode is ChannelMode.what_they_really_think
    assert einstein.subject == "Einstein"
    assert einstein.company == ""
    assert einstein.arena == ""


def test_quietly_and_why_everyone_patterns():
    aws = analyze_takeover_title("How AWS Quietly Took Over the Internet")
    assert aws.subject == "AWS"
    assert "internet" in aws.arena.lower()
    zoom = analyze_takeover_title("Why Everyone Started Using Zoom")
    assert zoom.subject == "Zoom"


def test_takeover_visual_types_include_flywheels():
    assert "FLYWHEEL_DIAGRAM" in TAKEOVER_VISUAL_TYPES
    assert "COMPETITOR_COMPARISON" in TAKEOVER_VISUAL_TYPES
    assert "MOAT_VISUAL" in TAKEOVER_VISUAL_TYPES
    assert "MONEY_FLOW" not in TAKEOVER_VISUAL_TYPES


def test_score_and_suggest_takeover_titles():
    scored = score_takeover_title("How Nvidia Took Over AI")
    assert scored["title_score"] >= 7
    assert "transformation_strength" in scored
    suggestions = suggest_takeover_titles("Nvidia", y="AI")
    assert suggestions
    assert any("Took Over" in row["title"] for row in suggestions)


def test_originality_indexes_are_split_three_ways():
    htto = recent_slugs(channel_mode="how_they_took_over")
    btb = recent_slugs(channel_mode="behind_the_business")
    wtrt = recent_slugs(channel_mode="what_they_really_think")
    assert "visa-really-makes-money" in btb
    assert "visa-really-makes-money" not in htto
    assert "visa-really-makes-money" not in wtrt
    assert "einstein-religion" not in htto
    assert mode_for_slug("visa-really-makes-money") is ChannelMode.behind_the_business
    assert mode_for_slug("einstein-religion") is ChannelMode.what_they_really_think


def _htto_project() -> VideoProject:
    analysis = analyze_title(
        "How Nvidia Took Over AI",
        channel_mode="how_they_took_over",
    )
    payoff = "They were already building the platform when the boom arrived."
    hook = (
        "Nvidia started as a company trying to make better graphics for games. "
        "Today some of the world's most advanced systems depend on its chips. "
        "Why was that even possible?"
    )
    body = (
        "The market before them was a graphics fight, not an AI platform. "
        "Then they made a bet that looked small at the time. "
        "Competitors noticed, but switching later meant rewriting software too. "
        "That is the flywheel, not a slogan. "
    )
    plan = StoryPlan(
        hook=hook,
        central_question=analysis.core_question,
        initial_assumption="It was just a graphics-chip company.",
        first_reveal="The tools around the chips started to matter more than the chips.",
        major_contradiction="A games company ended up at the center of AI.",
        turning_point="Demand arrived after the platform was already there.",
        final_answer=payoff,
        title_payoff=payoff,
        next_video_bridge="Almost every advanced chip still has to be manufactured somewhere.",
        signature_prop="the green board",
        chapters=[
            Chapter(name="The Gap", purpose=ScenePurpose.hook, narration=body),
            Chapter(name="The Bet", purpose=ScenePurpose.question, narration=body),
            Chapter(name="The War", purpose=ScenePurpose.escalation, narration=body),
            Chapter(name="The Loop", purpose=ScenePurpose.evidence, narration=body),
            Chapter(name="The Moat", purpose=ScenePurpose.reveal, narration=body),
            Chapter(name="The Threat", purpose=ScenePurpose.resolution, narration=body + " " + payoff),
        ],
    )
    return VideoProject(
        title=analysis.title,
        slug=slugify(analysis.title),
        channel_mode=ChannelMode.how_they_took_over,
        analysis=analysis,
        takeover=TakeoverContext(
            subject="Nvidia",
            arena="AI computing",
            starting_position="graphics-chip company",
            current_position="major AI computing platform",
            competitors=[
                CompetitorNote(
                    name="a rival chipmaker",
                    why_subject_won="software around the hardware",
                    why_they_lost_ground="different incentives, not stupidity",
                )
            ],
            turning_points=[
                TurningPoint(label="programmable graphics", impact="high", relevance="high")
            ],
            flywheels=[Flywheel(name="developer loop", steps=["tools", "software", "customers"])],
            threats=["new accelerators"],
            related_subject="a chip manufacturer",
        ),
        research=ResearchPack(
            subject=analysis.subject,
            target=analysis.target,
            fiscal_period="FY2025",
            claims=[
                Claim(
                    claim_id="tp_001",
                    claim="In fiscal 2025 data-center demand was a large share of revenue.",
                    kind=EvidenceKind.historian_interprets,
                    sources=[SourceRef(title="FY2025 Annual Report", kind="10-K")],
                    confidence="high",
                    fiscal_period="FY2025",
                )
            ],
            contradictions=["games company / AI dependence"],
        ),
        story=plan,
        scenes=[
            Scene(
                scene_id="scene_000",
                narration=hook,
                purpose=ScenePurpose.hook,
                visual_type="ORIGIN_SCENE",
                action="Wide workshop of graphics boards, no logos.",
                composition="wide shot",
                who="empty",
            )
        ],
    )


def test_htto_draft_metadata_is_not_a_portrait_or_money_flow():
    project = _htto_project()
    meta = draft_metadata(project)
    assert "Not investment advice" in meta.description
    assert "how they took over" in " ".join(meta.tags)
    assert "behind the business" not in " ".join(meta.tags)
    assert "flywheel" in meta.thumbnail_concept.lower() or "competitor" in meta.thumbnail_concept.lower()
    assert "30 percent" not in meta.thumbnail_concept
    assert meta.thumbnail_text != "THE REAL ENGINE"


def test_htto_compile_writes_mode_and_takeover_style(tmp_path: Path):
    project = _htto_project()
    written = compile_project(project, stubs_ok=True, root=tmp_path)
    spec = (tmp_path / "fixtures" / "video_specs" / "nvidia-took-over-ai.json").read_text(
        encoding="utf-8"
    )
    assert '"channel_mode": "how_they_took_over"' in spec
    assert "How They Took Over" in spec
    assert '"kokoro_speed": 1.15' in spec
    assert "behind_the_business" not in spec
    stills = Path(written["stills"]).read_text(encoding="utf-8")
    assert "How They Took Over" in stills
    assert "muted historical palette" not in stills
    assert "Behind The Business" not in stills
    jobs = json.loads(Path(written["jobs"]).read_text(encoding="utf-8"))
    for job in jobs["jobs"]:
        assert "Nvidia" not in job["prompt"]
    prompt = assemble_image_prompt(project, project.scenes[0])
    assert "How They Took Over" in prompt
    assert "What They Really Think" not in prompt
    assert "Behind The Business" not in prompt
    assert "Nvidia" not in prompt


def test_wtrt_spec_still_omits_takeover_assumptions():
    analysis = analyze_title("What Einstein Really Thought About Religion")
    project = VideoProject(
        title=analysis.title,
        slug="einstein-religion",
        analysis=analysis,
        story=StoryPlan(
            hook="He did not believe in a personal God, but he was not done with wonder.",
            central_question=analysis.core_question,
            initial_assumption="a",
            first_reveal="b",
            major_contradiction="c",
            turning_point="d",
            final_answer="e",
            title_payoff="He did not believe in a personal God, but he was not done with wonder.",
            next_video_bridge="next",
            chapters=[
                Chapter(name="The Word", purpose=ScenePurpose.hook, narration="n " * 200)
            ],
        ),
    )
    spec = spec_dict(project)
    assert spec["channel_mode"] == "what_they_really_think"
    assert spec["channel"] == "What They Really Think"
    assert "cuda" not in str(spec).lower()
    assert "flywheel" not in str(spec).lower()


def test_takeover_factcheck_rejects_unsourced_numbers():
    pack = ResearchPack(
        subject="Nvidia",
        target="AI",
        claims=[
            Claim(
                claim_id="fin_001",
                claim="Revenue was $130 billion.",
                kind=EvidenceKind.historian_interprets,
                sources=[],
                confidence="high",
            )
        ],
        contradictions=["graphics / AI"],
    )
    report = factcheck(pack, channel_mode="how_they_took_over")
    assert not report.ok
    assert "fin_001" in report.rejected_claim_ids


def test_htto_youtube_pack_uses_takeover_disclosure(tmp_path: Path):
    from channel.config import (
        BTB_HOST_ATTRIBUTION,
        HOST_ATTRIBUTION,
        HTTO_HOST_ATTRIBUTION,
        HTTO_YOUTUBE_DISCLOSURE,
    )
    from channel.youtube import write_pack

    spec = {
        "channel_mode": "how_they_took_over",
        "topic": "How Nvidia Took Over AI",
        "fixture": "fixtures/nvidia-took-over-ai.json",
        "youtube": {
            "title": "How Nvidia Took Over AI",
            "description": "How Nvidia took over AI: they were already building the platform.",
            "thumbnail_text": "THEY WERE READY",
            "short_title": "The Nvidia Decision That Changed AI",
            "tags": ["nvidia", "how they took over"],
        },
    }
    pack = write_pack(spec, root=tmp_path)
    desc = Path(pack["description"]).read_text(encoding="utf-8")
    assert HTTO_HOST_ATTRIBUTION in desc
    assert HTTO_YOUTUBE_DISCLOSURE in desc
    assert HOST_ATTRIBUTION not in desc
    assert BTB_HOST_ATTRIBUTION not in desc
    about = Path(pack["about"]).read_text(encoding="utf-8")
    assert "How They Took Over" in about
    assert pack["about"].endswith("how_they_took_over_about.txt")


def test_cli_analyze_takeover():
    from channel.__main__ import main

    assert main(["analyze", "--channel", "htto", "How Nvidia Took Over AI"]) == 0
    assert main(["score-title", "--channel", "how_they_took_over", "How Nvidia Took Over AI"]) == 0
    assert main(["suggest-titles", "--channel", "htto", "Nvidia", "--y", "AI"]) == 0
    assert main(["analyze", "--channel", "btb", "How Visa Really Makes Money"]) == 0
    assert main(["analyze", "What Einstein Really Thought About God"]) == 0
