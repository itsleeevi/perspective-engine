"""Score and suggest Behind The Business titles. Research still has to verify."""

from __future__ import annotations

from channel.schema import TitleAnalysis

TITLE_SCORE_DIMENSIONS = (
    "fame_recognition",
    "curiosity_gap",
    "business_surprise",
    "broad_appeal",
    "search_discovery",
    "thumbnail_potential",
    "source_availability",
    "story_depth",
    "advertiser_friendly",
    "evergreen_value",
)

TITLE_PATTERNS = (
    "How {x} Really Makes Money",
    "Why {x} Does {y}",
    "The Business Behind {x}",
    "How {x} Became So Powerful",
    "Why {x} Is So Hard to Compete With",
    "How {x} Keeps You Paying",
    "How {x} Makes Money From {y}",
    "The Strange Business Model Behind {x}",
    "Why {x} Is Everywhere",
    "How {x} Built a Monopoly-Like Advantage",
    "Why {x} Can Sell So Cheaply",
    "How {x} Turned {y} Into Billions",
    "The Hidden Economics of {x}",
)

TOPIC_CLUSTERS = (
    "PAYMENTS",
    "TECH_GIANTS",
    "AI",
    "RETAIL",
    "SAAS",
    "MARKETPLACES",
    "TRANSPORTATION",
    "LUXURY",
    "FOOD",
    "FINANCE",
    "SUBSCRIPTIONS",
    "E_COMMERCE",
    "LOGISTICS",
    "ADVERTISING",
    "CLOUD",
    "ENTERTAINMENT",
)

_EVERGREEN_MARKERS = (
    "makes money",
    "business behind",
    "hidden economics",
    "business model",
    "why",
    "how",
)
_NEWSY_MARKERS = ("stock fell", "yesterday", "this week", "earnings miss", "just announced")
_AD_FRIENDLY = (
    "software",
    "payments",
    "retail",
    "saas",
    "cloud",
    "marketplace",
    "subscription",
    "logistics",
    "ai",
    "technology",
)
_THIN_MARKERS = ("stock", "price target", "will explode")


def score_business_title(
    title: str,
    *,
    analysis: TitleAnalysis | None = None,
    known_company: bool = True,
    source_availability: int = 7,
) -> dict[str, int | float | str]:
    """Heuristic 1–10 scores. Agents may override after research."""
    lower = title.lower()
    fame = 8 if known_company else 4
    curiosity = 8 if lower.startswith(("how ", "why ", "the ")) else 5
    if "really" in lower or "hidden" in lower or "strange" in lower:
        curiosity = min(10, curiosity + 1)
    surprise = 7 if "why" in lower or "really" in lower else 6
    appeal = 8 if known_company else 5
    search = 8 if "makes money" in lower or "why" in lower else 6
    thumb = 8 if known_company else 5
    sources = max(1, min(10, source_availability))
    if any(m in lower for m in _THIN_MARKERS):
        sources = min(sources, 4)
    depth = 8 if "why" in lower or "how" in lower else 6
    ads = 8
    if any(m in lower for m in _AD_FRIENDLY):
        ads = 9
    evergreen = 8 if any(m in lower for m in _EVERGREEN_MARKERS) else 6
    if any(m in lower for m in _NEWSY_MARKERS):
        evergreen = 3
        curiosity = min(curiosity, 6)
    scores = {
        "fame_recognition": fame,
        "curiosity_gap": curiosity,
        "business_surprise": surprise,
        "broad_appeal": appeal,
        "search_discovery": search,
        "thumbnail_potential": thumb,
        "source_availability": sources,
        "story_depth": depth,
        "advertiser_friendly": ads,
        "evergreen_value": evergreen,
    }
    title_score = round(sum(scores.values()) / len(scores), 1)
    caution = ""
    if sources <= 5:
        caution = "Weak source availability — recommend only after filings are confirmed."
    return {
        "title": title,
        "company": (analysis.company if analysis else "") or "",
        **scores,
        "title_score": title_score,
        "caution": caution,
    }


def suggest_business_titles(company: str, *, y: str = "") -> list[dict[str, int | float | str]]:
    """Fill title patterns for a company and score each. Research still verifies."""
    name = " ".join(company.split())
    if not name:
        raise ValueError("company is required")
    scored: list[dict[str, int | float | str]] = []
    for pattern in TITLE_PATTERNS:
        if "{y}" in pattern and not y:
            continue
        title = pattern.format(x=name, y=y)
        scored.append(score_business_title(title))
    scored.sort(key=lambda row: float(row["title_score"]), reverse=True)
    return scored


def adjacent_topics(cluster: str) -> list[str]:
    """Recommend a cluster, not a cloned story."""
    key = cluster.strip().upper().replace(" ", "_")
    if key not in TOPIC_CLUSTERS:
        return list(TOPIC_CLUSTERS)
    return [c for c in TOPIC_CLUSTERS if c != key]
