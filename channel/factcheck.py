"""Agent 3 — Fact checker (mechanical). The Cursor agent still reviews history."""

from __future__ import annotations

from channel.schema import Claim, EvidenceKind, FactCheckReport, ResearchPack


def factcheck(pack: ResearchPack) -> FactCheckReport:
    flags: list[str] = []
    rejected: list[str] = []
    if pack.insufficient_evidence:
        flags.append("research marked insufficient_evidence — story must say so")
    if not pack.claims:
        flags.append("no verified claims yet — agent must add sourced claims")
    for claim in pack.claims:
        issues = _claim_issues(claim)
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
