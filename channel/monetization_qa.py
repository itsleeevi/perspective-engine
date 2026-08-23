"""Monetization readiness score — human-like editorial quality gate."""

from __future__ import annotations

from channel.config import CHANNEL
from channel.factcheck import factcheck
from channel.originality_policy import GENERIC_AI_PHRASES, MONETIZATION_THRESHOLDS
from channel.qa import mechanical_qa, narration_of, word_count
from channel.schema import MonetizationReadiness, OriginalityReport, VideoProject


def _clamp(n: float, lo: int = 1, hi: int = 10) -> int:
    return max(lo, min(hi, int(round(n))))


def compute_monetization_readiness(
    project: VideoProject,
    originality: OriginalityReport | None = None,
) -> MonetizationReadiness:
    """Build the final internal QA object before publish."""
    scores = project.qa or mechanical_qa(project)
    report = factcheck(project.research)
    text = narration_of(project)
    lower = text.lower()
    notes: list[str] = []

    claims = project.research.claims
    sourced = sum(1 for c in claims if c.sources)
    if not claims:
        original_research = 3
        notes.append("no research claims yet")
    elif sourced / len(claims) >= 0.8:
        original_research = 9
    elif sourced / len(claims) >= 0.5:
        original_research = 7
        notes.append("some claims lack source URLs")
    else:
        original_research = 4
        notes.append("most claims lack sources")

    if report.ok:
        source_quality = 9
    elif report.rejected_claim_ids:
        source_quality = 4
        notes.append(f"factcheck rejected {len(report.rejected_claim_ids)} claims")
    else:
        source_quality = 6

    orig_score = originality.originality_score if originality else 100.0
    story_originality = _clamp(orig_score / 10.0)
    generic_hits = len([p for p in GENERIC_AI_PHRASES if p in lower])
    narration_originality = _clamp((scores.clarity or 8) - generic_hits)

    visual_originality = 8
    if originality and originality.flags:
        if any("visual variety" in f for f in originality.flags):
            visual_originality = 5

    educational_value = _clamp(
        (scores.story or 5)
        + (1 if project.story and project.story.major_contradiction else 0)
        + (1 if project.story and project.story.title_payoff in text else 0)
        - (
            1
            if project.research.insufficient_evidence
            and not project.research.insufficient_note
            else 0
        )
    )

    retention_quality = _clamp(
        ((scores.hook or 0) + (scores.curiosity or 0) + (scores.pacing or 0)) / 3.0
    )

    character_consistency = 8
    if project.scenes and project.characters:
        for scene in project.scenes:
            for cid in scene.characters:
                if cid not in project.characters:
                    character_consistency = 5
                    notes.append(f"scene {scene.scene_id} references unknown {cid}")

    mass_production_risk = _clamp(
        max(1.0, (100.0 - orig_score) / 10.0 + len(originality.flags) * 0.5)
        if originality
        else 1
    )

    positive = (
        original_research
        + story_originality
        + narration_originality
        + visual_originality
        + educational_value
        + source_quality
        + character_consistency
        + retention_quality
    )
    overall = int(round(positive / 8.0 * 10.0 - (mass_production_risk - 1) * 5))
    overall = max(0, min(100, overall))

    thresholds = MONETIZATION_THRESHOLDS
    ready = (
        original_research >= thresholds["original_research_min"]
        and story_originality >= thresholds["story_originality_min"]
        and narration_originality >= thresholds["narration_originality_min"]
        and educational_value >= thresholds["educational_value_min"]
        and retention_quality >= thresholds["retention_quality_min"]
        and mass_production_risk <= thresholds["mass_production_risk_max"]
        and overall >= thresholds["overall_min"]
        and report.ok
        and (originality.ready_for_images if originality else True)
    )

    if not report.ok:
        notes.append("factcheck not ok")
    if originality and not originality.ready_for_images:
        notes.extend(originality.flags[:3])

    words = word_count(text)
    if words and words < CHANNEL.narration_word_min:
        notes.append(f"narration {words} words below {CHANNEL.narration_word_min}")

    return MonetizationReadiness(
        original_research=original_research,
        story_originality=story_originality,
        narration_originality=narration_originality,
        visual_originality=visual_originality,
        educational_value=educational_value,
        source_quality=source_quality,
        character_consistency=character_consistency,
        retention_quality=retention_quality,
        mass_production_risk=mass_production_risk,
        overall=overall,
        ready_to_publish=ready,
        originality_score=orig_score,
        notes=notes,
    )
