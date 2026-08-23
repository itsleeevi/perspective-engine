"""Agent 3 — Fact checker (mechanical). The Cursor agent still reviews history."""

from __future__ import annotations

import re

from channel.modes import ChannelMode, is_business
from channel.schema import Claim, EvidenceKind, FactCheckReport, ResearchPack

_FINANCIAL = re.compile(
    r"\$[\d,.]+|\b\d{1,3}(?:\.\d+)?\s*%|\b(?:billion|million|trillion)\b",
    re.I,
)


def factcheck(
    pack: ResearchPack,
    *,
    channel_mode: ChannelMode | str | None = None,
) -> FactCheckReport:
    flags: list[str] = []
    rejected: list[str] = []
    if pack.insufficient_evidence:
        flags.append("research marked insufficient_evidence — story must say so")
    if not pack.claims:
        flags.append("no verified claims yet — agent must add sourced claims")
    for claim in pack.claims:
        issues = _claim_issues(claim)
        if is_business(channel_mode):
            issues.extend(_financial_issues(claim, pack))
        if issues:
            rejected.append(claim.claim_id)
            flags.extend(f"{claim.claim_id}: {i}" for i in issues)
    if pack.claims and not pack.contradictions:
        flags.append("no contradictions listed — look harder before writing")
    ok = bool(pack.claims) and not rejected
    return FactCheckReport(ok=ok, flags=flags, rejected_claim_ids=rejected)


def _claim_issues(claim: Claim) -> list[str]:
    issues: list[str] = []
    if claim.is_direct_quote or claim.quote:
        if not claim.quote.strip():
            issues.append("direct quote flag with empty quote")
        if not claim.sources:
            issues.append("quote has no source")
        if claim.kind not in (EvidenceKind.said, EvidenceKind.wrote):
            issues.append("quote must be kind=said or wrote, not a paraphrase")
    if claim.confidence == "disputed" and "disputed" not in claim.claim.lower():
        issues.append("disputed claim must be qualified in the claim text")
    if not claim.sources and claim.confidence == "high":
        issues.append("high confidence requires at least one source")
    return issues


def _financial_issues(claim: Claim, pack: ResearchPack) -> list[str]:
    issues: list[str] = []
    if not _FINANCIAL.search(claim.claim):
        return issues
    if not claim.sources:
        issues.append("financial figure has no source — do not invent numbers")
    if not (claim.fiscal_period or pack.fiscal_period or claim.date):
        issues.append("financial figure needs fiscal_period or a dated source")
    if claim.calculation and not claim.inputs and not claim.sources:
        issues.append("derived number needs calculation inputs or sources")
    return issues
