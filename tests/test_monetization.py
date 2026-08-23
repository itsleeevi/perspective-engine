"""Monetization readiness gate."""

from channel.monetization_qa import compute_monetization_readiness
from channel.originality_policy import MONETIZATION_THRESHOLDS
from channel.schema import (
    Claim,
    EvidenceKind,
    OriginalityReport,
    ResearchPack,
    SourceRef,
    StoryPlan,
    TitleAnalysis,
    VideoProject,
)


def _project(*, with_claims: bool = True) -> VideoProject:
    claims = []
    if with_claims:
        claims = [
            Claim(
                claim_id="c1",
                claim="He wrote a letter.",
                kind=EvidenceKind.wrote,
                sources=[SourceRef(title="Letter", url="https://example.com", source_type="letter")],
                confidence="high",
            )
        ]
    return VideoProject(
        title="What Test Really Thought About Example",
        slug="test-example",
        analysis=TitleAnalysis(
            title="What Test Really Thought About Example",
            subject="Test",
            target="Example",
            verb="Thought",
            core_question="What did Test really think about Example?",
        ),
        research=ResearchPack(
            subject="Test",
            target="Example",
            claims=claims,
            contradictions=["public yes, private no"],
        ),
        story=StoryPlan(
            hook="The letter sat on the table and he would not open it.",
            central_question="What did he think?",
            initial_assumption="People thought he agreed.",
            first_reveal="The letter said otherwise.",
            major_contradiction="He signed the deal and then wrote against it.",
            turning_point="The second letter.",
            final_answer="He thought Example was a tool, not a friend.",
            title_payoff="He thought Example was a tool, not a friend.",
            next_video_bridge="The next question is what Example thought back.",
            chapters=[],
        ),
    )


def test_empty_research_is_not_ready_to_publish():
    project = _project(with_claims=False)
    ready = compute_monetization_readiness(project)
    assert ready.original_research < MONETIZATION_THRESHOLDS["original_research_min"]
    assert ready.ready_to_publish is False


def test_sourced_claims_raise_the_research_score():
    empty = compute_monetization_readiness(_project(with_claims=False))
    sourced = compute_monetization_readiness(
        _project(),
        OriginalityReport(slug="test-example", originality_score=90, ready_for_images=True),
    )
    assert sourced.original_research >= 8
    assert sourced.original_research > empty.original_research


def test_low_originality_blocks_publish():
    ready = compute_monetization_readiness(
        _project(),
        OriginalityReport(
            slug="test-example",
            originality_score=40,
            ready_for_images=False,
            flags=["too close to other-title"],
        ),
    )
    assert ready.mass_production_risk > 3
    assert ready.ready_to_publish is False
