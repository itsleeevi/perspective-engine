"""Behind The Business mode — must not leak into What They Really Think."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from channel.business_title import analyze_business_title
from channel.business_titles import score_business_title, suggest_business_titles
from channel.business_visuals import BUSINESS_VISUAL_TYPES, MONEY_FLOW_COMPONENTS
from channel.metadata import draft_metadata
from channel.originality import mode_for_slug
from channel.compile import compile_project, spec_dict
from channel.config import (
    BEHIND_THE_BUSINESS,
    BEHIND_THE_BUSINESS_VISUAL_STYLE,
    CHANNEL,
    GLOBAL_VISUAL_STYLE,
    config_for,
    kokoro_speed_for,
    kokoro_voice_for,
)
from channel.factcheck import factcheck
from channel.modes import ChannelMode, parse_mode
from channel.originality import recent_slugs
from channel.prompts import assemble_image_prompt
from channel.qa import mechanical_qa
from channel.schema import (
    BusinessContext,
    Chapter,
    Claim,
    EvidenceKind,
    ResearchPack,
    Scene,
    ScenePurpose,
    SourceRef,
    StoryPlan,
    TitleAnalysis,
    VideoProject,
)
from channel.slug import slugify
from channel.title import analyze_title


def test_wtrt_defaults_unchanged():
    assert CHANNEL.mode is ChannelMode.what_they_really_think
    assert CHANNEL.name == "What They Really Think"
    assert CHANNEL.target_duration_seconds == 1380
    assert CHANNEL.narration_word_min == 4400
    assert CHANNEL.narration_word_max == 5500
    assert CHANNEL.narration_wpm == 200
    assert CHANNEL.kokoro_speed == 1.15
    assert CHANNEL.visual_style == GLOBAL_VISUAL_STYLE
    assert config_for(None) is CHANNEL
    assert config_for("what_they_really_think") is CHANNEL


def test_btb_config_is_a_different_channel():
    cfg = config_for("behind_the_business")
    assert cfg is BEHIND_THE_BUSINESS
    assert cfg.name == "How They Really Make Money"
    assert cfg.target_duration_seconds == 1320
    assert cfg.narration_word_min == 4400
    assert cfg.narration_word_max == 5500
    assert cfg.narration_wpm == 200
    assert cfg.kokoro_speed == 1.15
    assert cfg.visual_style == BEHIND_THE_BUSINESS_VISUAL_STYLE
    assert "muted historical" not in cfg.visual_style
    assert "What They Really Think" not in cfg.visual_style
    assert CHANNEL.visual_style != cfg.visual_style
    assert cfg.channel_handle == "@HowTheyReallyMakeMoney"
    assert "Not investment advice" in cfg.channel_about


def test_visa_recut_locks_liam_at_115():
    assert kokoro_voice_for("visa-really-makes-money") == "am_liam"
    assert kokoro_speed_for("visa-really-makes-money", BEHIND_THE_BUSINESS) == 1.15
    assert kokoro_voice_for("costco-really-makes-money") == "am_liam"
    assert kokoro_speed_for("costco-really-makes-money", BEHIND_THE_BUSINESS) == 0.92


def test_new_titles_use_kokoro_at_least_1():
    from channel.locks import KOKORO_SPEED_MAX, KOKORO_SPEED_MIN

    assert CHANNEL.kokoro_speed >= KOKORO_SPEED_MIN
    assert CHANNEL.kokoro_speed <= KOKORO_SPEED_MAX
    assert BEHIND_THE_BUSINESS.kokoro_speed >= KOKORO_SPEED_MIN
    assert BEHIND_THE_BUSINESS.kokoro_speed <= KOKORO_SPEED_MAX
    assert kokoro_speed_for("acme-really-makes-money", BEHIND_THE_BUSINESS) == 1.15
    assert kokoro_speed_for("what-someone-really-thought", CHANNEL) == 1.15


def test_parse_mode_aliases():
    assert parse_mode("btb") is ChannelMode.behind_the_business
    assert parse_mode("wtrt") is ChannelMode.what_they_really_think
    with pytest.raises(ValueError):
        parse_mode("tiktok")


def test_wtrt_analyze_title_needs_no_channel_arg():
    a = analyze_title("What Einstein Really Thought About God")
    assert a.subject == "Einstein"
    assert a.target == "God"
    assert a.verb == "Thought"
    assert a.channel_mode is ChannelMode.what_they_really_think
    assert a.company == ""
    assert a.potential_hidden_engine == ""


def test_business_title_without_mode_is_rejected_with_hint():
    with pytest.raises(ValueError, match="behind_the_business"):
        analyze_title("How Costco Really Makes Money")


def test_wtrt_title_rejected_in_business_mode():
    with pytest.raises(ValueError, match="What They Really Think"):
        analyze_title(
            "What Einstein Really Thought About God",
            channel_mode="behind_the_business",
        )


def test_costco_title_does_not_assume_membership():
    a = analyze_title(
        "How Costco Really Makes Money",
        channel_mode="behind_the_business",
    )
    blob = " ".join(
        [
            a.apparent_business,
            a.potential_hidden_engine,
            a.industry,
            a.business_question,
            *a.likely_revenue_streams,
        ]
    ).lower()
    assert a.company == "Costco"
    assert a.subject == "Costco"
    assert a.verb is None
    assert a.channel_mode is ChannelMode.behind_the_business
    assert "membership" not in blob
    assert "unknown until researched" in a.potential_hidden_engine
    assert "economic profit" in a.business_question.lower()


def test_visa_title_is_a_different_question():
    costco = analyze_title(
        "How Costco Really Makes Money",
        channel_mode=ChannelMode.behind_the_business,
    )
    visa = analyze_title(
        "How Visa Really Makes Money",
        channel_mode="btb",
    )
    assert visa.company == "Visa"
    assert visa.business_question != costco.business_question
    assert "visa" in visa.business_question.lower()
    assert "costco" not in visa.business_question.lower()


def test_why_and_the_patterns():
    why = analyze_business_title("Why Airlines Intentionally Sell Too Many Tickets")
    assert why.company == "Airlines"
    assert why.core_question.startswith("Why")
    hidden = analyze_business_title("The Hidden Economics of Luxury Brands")
    assert "Luxury Brands" in hidden.company
    assert "real business" in hidden.core_question.lower()


def test_multiword_and_trailing_money_titles():
    credit = analyze_business_title("How Credit Card Companies Really Make Money")
    assert credit.company == "Credit Card Companies"
    assert "Companies's" not in credit.business_question
    assert "Companies'" in credit.business_question
    luxury = analyze_business_title("How Luxury Brands Turn Scarcity Into Billions")
    assert luxury.company == "Luxury Brands"
    visa = analyze_business_title("How Visa Makes Money Every Time You Buy Something")
    assert visa.company == "Visa"
    assert "every time" in visa.business_question.lower()
    adobe = analyze_business_title("Why Adobe Wants You to Pay Forever")
    assert adobe.company == "Adobe"
    ikea = analyze_business_title("Why IKEA Makes You Walk Through the Entire Store")
    assert ikea.company == "IKEA"


def test_slugify_keeps_wtrt_and_supports_business():
    assert slugify("What Einstein Really Thought About Religion") == "einstein-religion"
    assert slugify("How Costco Really Makes Money") == "costco-really-makes-money"
    assert slugify("Why Costco Barely Marks Up Its Products").startswith("why-costco")


def test_title_scorer_returns_all_dimensions():
    scored = score_business_title("How Costco Really Makes Money")
    assert scored["title_score"] >= 6
    for key in (
        "fame_recognition",
        "curiosity_gap",
        "business_surprise",
        "source_availability",
        "evergreen_value",
    ):
        assert 1 <= int(scored[key]) <= 10


def test_suggest_titles_scores_patterns_for_a_company():
    rows = suggest_business_titles("Costco")
    titles = [row["title"] for row in rows]
    assert "How Costco Really Makes Money" in titles
    assert "The Hidden Economics of Costco" in titles
    assert all("title_score" in row for row in rows)
    with_y = suggest_business_titles("Visa", y="swipes")
    assert any("From swipes" in row["title"] for row in with_y)


def test_visual_components_are_catalogued():
    assert "MONEY_FLOW" in BUSINESS_VISUAL_TYPES
    assert "membership" in MONEY_FLOW_COMPONENTS
    assert "customer" in MONEY_FLOW_COMPONENTS


def test_derived_financial_claim_needs_inputs():
    pack = ResearchPack(
        subject="Visa",
        target="how the company makes money",
        fiscal_period="FY2025",
        claims=[
            Claim(
                claim_id="fin_002",
                claim="Take-rate is 0.2% of volume.",
                kind=EvidenceKind.historian_interprets,
                sources=[SourceRef(title="FY2025 10-K", kind="10-K")],
                confidence="high",
                fiscal_period="FY2025",
                calculation="network revenue / payment volume",
                inputs=["network revenue", "payment volume"],
            )
        ],
        contradictions=["volume vs profit"],
    )
    assert factcheck(pack, channel_mode="behind_the_business").ok


def test_financial_claim_without_source_is_rejected():
    pack = ResearchPack(
        subject="Costco",
        target="how the company makes money",
        claims=[
            Claim(
                claim_id="fin_001",
                claim="Revenue was $250 billion.",
                kind=EvidenceKind.historian_interprets,
                sources=[],
                confidence="high",
            )
        ],
        contradictions=["thin product margins / large profit"],
    )
    report = factcheck(pack, channel_mode="behind_the_business")
    assert not report.ok
    assert "fin_001" in report.rejected_claim_ids


def test_wtrt_factcheck_does_not_require_fiscal_period():
    pack = ResearchPack(
        subject="Einstein",
        target="God",
        claims=[
            Claim(
                claim_id="claim_001",
                claim='He wrote "I do not believe."',
                kind=EvidenceKind.wrote,
                is_direct_quote=True,
                quote="I do not believe.",
                sources=[SourceRef(title="Letter", kind="primary")],
                confidence="high",
            )
        ],
        contradictions=["public vs private"],
    )
    assert factcheck(pack).ok


def test_originality_indexes_are_split():
    btb = recent_slugs(channel_mode="behind_the_business")
    assert "costco-really-makes-money" in btb
    assert "visa-really-makes-money" in btb
    wtrt = recent_slugs(channel_mode="what_they_really_think")
    assert wtrt  # shipped history cuts exist
    assert "visa-really-makes-money" not in wtrt
    assert "costco-really-makes-money" not in wtrt
    assert mode_for_slug("einstein-religion") is ChannelMode.what_they_really_think
    assert mode_for_slug("visa-really-makes-money") is ChannelMode.behind_the_business
    assert mode_for_slug("costco-really-makes-money") is ChannelMode.behind_the_business


def _btb_project() -> VideoProject:
    analysis = analyze_title(
        "How Costco Really Makes Money",
        channel_mode="behind_the_business",
    )
    payoff = "The warehouse is the bait. The card is the business."
    hook = (
        "Costco sells billions of dollars of products and barely wants to "
        "profit from many of them. The real engine is much smaller."
    )
    body = (
        "Shoppers see pallets and low prices. That is the obvious store. "
        "The strange part is how little the store itself is allowed to earn. "
        "A dated filing shows product margins staying thin on purpose. "
        "Members pay before they buy. That is the question the numbers have to answer. "
    )
    plan = StoryPlan(
        hook=hook,
        central_question=analysis.core_question,
        initial_assumption="It is a grocery warehouse.",
        first_reveal="Product margins are a strategy, not a failure.",
        major_contradiction="Huge sales, thin product profit.",
        turning_point="The membership fee does a different job than the till.",
        final_answer=payoff,
        title_payoff=payoff,
        next_video_bridge="Another famous chain built a different machine.",
        signature_prop="the membership card",
        chapters=[
            Chapter(name="The Pallets", purpose=ScenePurpose.hook, narration=body),
            Chapter(name="Thin Prices", purpose=ScenePurpose.question, narration=body),
            Chapter(name="The Card", purpose=ScenePurpose.reveal, narration=body),
            Chapter(name="The Loop", purpose=ScenePurpose.evidence, narration=body),
            Chapter(name="Copycats Fail", purpose=ScenePurpose.escalation, narration=body),
            Chapter(name="The Real Till", purpose=ScenePurpose.resolution, narration=body + " " + payoff),
        ],
    )
    return VideoProject(
        title=analysis.title,
        slug=slugify(analysis.title),
        channel_mode=ChannelMode.behind_the_business,
        analysis=analysis,
        business=BusinessContext(
            company="Costco",
            industry="retail",
            business_question=analysis.business_question,
            apparent_business="warehouse retail",
            potential_hidden_engine="unknown until researched",
        ),
        research=ResearchPack(
            subject=analysis.subject,
            target=analysis.target,
            fiscal_period="FY2025",
            claims=[
                Claim(
                    claim_id="fin_001",
                    claim="In fiscal 2025 membership fees were a small share of sales and a large share of profit.",
                    kind=EvidenceKind.historian_interprets,
                    sources=[SourceRef(title="FY2025 Annual Report", kind="10-K")],
                    confidence="high",
                    fiscal_period="FY2025",
                )
            ],
            contradictions=["thin product margins / high membership value"],
        ),
        story=plan,
        scenes=[
            Scene(
                scene_id="scene_000",
                narration=hook,
                purpose=ScenePurpose.hook,
                visual_type="WAREHOUSE_SCENE",
                action="Wide warehouse aisle of bulk pallets, no logos.",
                composition="wide shot",
                who="empty",
            )
        ],
    )


def test_btb_mechanical_qa_uses_business_word_budget():
    project = _btb_project()
    scores = mechanical_qa(project)
    assert any("4400" in n or "words" in n for n in scores.notes) or scores.pacing <= 8


def test_btb_draft_metadata_includes_sources_and_disclaimer():
    project = _btb_project()
    meta = draft_metadata(project)
    assert "Not investment advice" in meta.description
    assert "FY2025 Annual Report" in meta.description
    assert "Related:" in meta.description
    assert "how they really make money" in " ".join(meta.tags)


def test_btb_compile_writes_mode_and_business_style(tmp_path: Path):
    project = _btb_project()
    written = compile_project(project, stubs_ok=True, root=tmp_path)
    spec = (tmp_path / "fixtures" / "video_specs" / "costco-really-makes-money.json").read_text(
        encoding="utf-8"
    )
    assert '"channel_mode": "behind_the_business"' in spec
    assert "How They Really Make Money" in spec
    assert '"kokoro_speed": 0.92' in spec  # shipped Costco lock
    assert '"narration_wpm": 200' in spec
    stills = Path(written["stills"]).read_text(encoding="utf-8")
    assert "Behind The Business" in stills
    assert "muted historical palette" not in stills
    jobs = json.loads(Path(written["jobs"]).read_text(encoding="utf-8"))
    for job in jobs["jobs"]:
        assert "Costco" not in job["prompt"]
    prompt = assemble_image_prompt(project, project.scenes[0])
    assert "Behind The Business" in prompt
    assert "What They Really Think" not in prompt
    assert "Costco" not in prompt


def test_wtrt_spec_still_omits_business_assumptions():
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
    assert spec["kokoro_speed"] == 1.15
    assert "membership" not in str(spec).lower()


def test_config_py_has_no_company_examples():
    text = Path("channel/config.py").read_text(encoding="utf-8").lower()
    for name in ("costco", "visa", "mcdonald", "netflix", "spotify", "nvidia", "rolex"):
        assert name not in text, f"{name} leaked into channel/config.py"


def test_cli_score_and_suggest_titles():
    from channel.__main__ import main

    assert main(["score-title", "How Costco Really Makes Money"]) == 0
    assert main(["suggest-titles", "Visa", "--y", "swipes"]) == 0
    assert main(["analyze", "--channel", "btb", "How Visa Really Makes Money"]) == 0
    assert main(["analyze", "What Einstein Really Thought About God"]) == 0
