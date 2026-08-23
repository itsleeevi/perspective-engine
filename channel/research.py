"""Agent 2 — Researcher seed.

Pulls a free encyclopedia summary so the Cursor agent has a starting pack.
Primary-source work is still the agent's job; this must not be the only source.
"""

from __future__ import annotations

import httpx

from channel.modes import ChannelMode
from channel.schema import ResearchPack, SourceRef, TitleAnalysis

_API = "https://en.wikipedia.org/w/api.php"
_UA = "WhatTheyReallyThink/0.1 (local documentary research seed)"
_UA_BTB = "BehindTheBusiness/0.1 (local documentary research seed)"


def _search(query: str, client: httpx.Client) -> list[dict]:
    r = client.get(
        _API,
        params={
            "action": "query",
            "list": "search",
            "srsearch": query,
            "srlimit": 5,
            "format": "json",
        },
    )
    r.raise_for_status()
    return list(r.json().get("query", {}).get("search", []))


def _extract(title: str, client: httpx.Client) -> str:
    r = client.get(
        _API,
        params={
            "action": "query",
            "prop": "extracts",
            "exintro": 1,
            "explaintext": 1,
            "titles": title,
            "format": "json",
        },
    )
    r.raise_for_status()
    pages = r.json().get("query", {}).get("pages", {})
    for page in pages.values():
        return str(page.get("extract") or "")
    return ""


def seed_research(analysis: TitleAnalysis, *, timeout: float = 20.0) -> ResearchPack:
    """Encyclopedia seed. Claims list stays empty until the agent verifies."""
    business = analysis.channel_mode is ChannelMode.behind_the_business
    if business:
        company = analysis.company or analysis.subject
        queries = [
            f"{company} 10-K",
            f"{company} annual report",
            f"{company} business model",
            company,
        ]
    else:
        queries = [
            f"{analysis.subject} {analysis.target}",
            analysis.subject,
            analysis.target,
        ]
    sources: list[SourceRef] = []
    extracts: list[str] = []
    try:
        with httpx.Client(
            timeout=timeout, headers={"User-Agent": _UA_BTB if business else _UA}
        ) as client:
            seen: set[str] = set()
            for q in queries:
                for hit in _search(q, client):
                    title = str(hit.get("title") or "")
                    if not title or title in seen:
                        continue
                    seen.add(title)
                    extract = _extract(title, client)
                    if extract:
                        extracts.append(extract[:1200])
                        sources.append(
                            SourceRef(
                                title=title,
                                url=f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}",
                                kind="encyclopedia_seed",
                                note="seed only — verify with primary sources",
                            )
                        )
                    if len(sources) >= 6:
                        break
                if len(sources) >= 6:
                    break
    except httpx.HTTPError as exc:
        return ResearchPack(
            subject=analysis.subject,
            target=analysis.target,
            summary=f"Encyclopedia seed failed ({exc}). Research must proceed from primary sources.",
            insufficient_evidence=True,
            insufficient_note="seed fetch failed",
        )
    summary = "\n\n".join(extracts)[:4000]
    return ResearchPack(
        subject=analysis.subject,
        target=analysis.target,
        summary=summary or "No encyclopedia extract. Research from primary sources.",
        seed_sources=sources,
        claims=[],
    )
