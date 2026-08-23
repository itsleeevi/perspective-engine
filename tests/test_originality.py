"""Mass-production detector and name-swap test."""

from channel.originality import (
    name_swap_too_close,
    originality_score_from_similarity,
    originality_report_for_slug,
    recent_slugs,
    regenerate_targets,
)
from channel.originality_policy import ORIGINALITY_SCORE_MIN, RECENT_VIDEO_COMPARE_COUNT
from channel.schema import OriginalityReport, SimilarityBreakdown


def test_recent_slugs_reads_index_newest_first():
    slugs = recent_slugs()
    assert slugs
    assert slugs[0] == "freud-women"
    assert len(slugs) <= RECENT_VIDEO_COMPARE_COUNT
    assert "freud-women" not in recent_slugs(exclude="freud-women")


def test_originality_score_inverts_similarity():
    assert originality_score_from_similarity(0) == 100.0
    assert originality_score_from_similarity(25) == 75.0
    assert originality_score_from_similarity(100) == 0.0


def test_shipped_freud_clears_the_originality_floor():
    report = originality_report_for_slug("freud-women")
    assert report.originality_score >= ORIGINALITY_SCORE_MIN
    assert report.ready_for_images


def test_name_swap_detects_interchangeable_payoff():
    assert name_swap_too_close(
        "He thought Einstein was a fraud about God.",
        "He thought Jobs was a fraud about Gates.",
        ["Einstein", "God", "Jobs", "Gates"],
    )
    assert not name_swap_too_close(
        "He thought a woman was a man who had lost something.",
        "He thought people are animals who learned to be kind.",
        ["Freud", "Women", "Darwin", "Human Nature"],
    )


def test_regenerate_targets_maps_flags_to_stages():
    report = OriginalityReport(
        slug="demo",
        originality_score=60,
        ready_for_images=False,
        flags=[
            "stock hook opener: 'is remembered as'",
            "visual variety: desk/map/newspaper",
            "originality_score 60 < 80",
        ],
        comparisons=[
            SimilarityBreakdown(
                compared_slug="other",
                hook=80,
                phrasing=20,
                thumbnail=90,
            )
        ],
    )
    targets = regenerate_targets(report)
    assert "hook" in targets
    assert "scenes" in targets
    assert "narration" in targets
    assert "thumbnail" in targets
