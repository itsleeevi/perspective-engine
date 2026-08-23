"""Score and suggest How They Took Over titles. Research still has to verify."""

from __future__ import annotations

from channel.schema import TitleAnalysis

TITLE_SCORE_DIMENSIONS = (
    "subject_recognition",
    "curiosity_gap",
    "transformation_strength",
    "competition",
    "story_depth",
    "thumbnail_potential",
    "source_availability",
    "evergreen_value",
    "advertiser_friendly",
    "broad_appeal",
)

TITLE_PATTERNS = (
    "How {x} Took Over {y}",
    "How {x} Became So Powerful",
    "How {x} Won the {y} War",
    "How {x} Built an Empire",
    "How {x} Became Impossible to Ignore",
    "How {x} Beat Everyone",
    "How {x} Became the Standard",
    "How {x} Changed an Entire Industry",
    "How {x} Went From {y} to Dominance",
    "How {x} Quietly Took Over {y}",
    "Why Everyone Started Using {x}",
    "How {x} Became a Global Giant",
)

TOPIC_CLUSTERS = (
    "AI",
    "BIG_TECH",
    "RETAIL",
    "E_COMMERCE",
    "STREAMING",
    "SOCIAL_MEDIA",
    "TRANSPORTATION",
    "AUTOMOTIVE",
    "LUXURY",
    "FOOD",
    "SPORTS_BUSINESS",
    "SOFTWARE",
    "SEMICONDUCTORS",
    "PAYMENTS",
    "MARKETPLACES",
    "GLOBAL_BRANDS",
    "ENTERTAINMENT",
    "LOGISTICS",
)

_EVERGREEN = ("took over", "became", "built", "won", "quietly", "everyone started")
_NEWSY = ("stock fell", "yesterday", "this week", "just announced")
_THIN = ("will explode", "destroyed everyone", "shocking move")
_AD_OK = (
    "software",
    "search",
    "retail",
    "streaming",
    "music",
    "cars",
    "phones",
    "chips",
    "cloud",
    "logistics",
)


def score_takeover_title(
    title: str,
    *,
    analysis: TitleAnalysis | None = None,
    known_subject: bool = True,
    source_availability: int = 7,
) -> dict[str, int | float | str]:
    raw = " ".join(title.strip().split())
    lower = raw.lower()
    fame = 8 if known_subject else 4
    curiosity = 8 if ("how" in lower or "why" in lower) else 5
    if any(w in lower for w in ("took over", "empire", "quietly", "everyone started")):
        curiosity = min(10, curiosity + 1)
    transform = (
        9
        if "took over" in lower or "became" in lower or "went from" in lower
        else 6
    )
    competition = 8 if any(w in lower for w in ("war", "beat", "won", "took over")) else 6
    depth = 8 if analysis and analysis.core_question else 6
    thumb = 8 if 3 <= len(raw.split()) <= 12 else 6
    sources = max(1, min(10, source_availability))
    evergreen = 9 if any(m in lower for m in _EVERGREEN) else 6
    if any(m in lower for m in _NEWSY):
        evergreen = 4
    ad = 8 if any(m in lower for m in _AD_OK) or "how" in lower else 7
    if any(m in lower for m in _THIN):
        ad = 3
        curiosity = min(curiosity, 4)
        sources = min(sources, 4)
    broad = 8 if fame >= 7 else 6
    scores = {
        "subject_recognition": fame,
        "curiosity_gap": curiosity,
        "transformation_strength": transform,
        "competition": competition,
        "story_depth": depth,
        "thumbnail_potential": thumb,
        "source_availability": sources,
        "evergreen_value": evergreen,
        "advertiser_friendly": ad,
        "broad_appeal": broad,
    }
    caution = ""
    if sources <= 5:
        caution = "Weak source availability — recommend only after primary sources are confirmed."
    return {
        "title": raw,
        "subject": (analysis.subject if analysis else "") or "",
        **scores,
        "title_score": round(sum(scores[k] for k in TITLE_SCORE_DIMENSIONS) / 10, 1),
        "caution": caution,
    }


def suggest_takeover_titles(subject: str, *, y: str = "") -> list[dict[str, int | float | str]]:
    name = " ".join(subject.split())
    if not name:
        raise ValueError("subject is required")
    arena = y.strip() or "the category"
    scored: list[dict[str, int | float | str]] = []
    for pattern in TITLE_PATTERNS:
        if "{y}" in pattern and not y:
            title = pattern.format(x=name, y=arena)
        else:
            title = pattern.format(x=name, y=arena)
        scored.append(score_takeover_title(title))
    scored.sort(key=lambda row: float(row["title_score"]), reverse=True)
    return scored


def adjacent_topics(cluster: str) -> list[str]:
    key = cluster.strip().upper().replace(" ", "_")
    if key not in TOPIC_CLUSTERS:
        return list(TOPIC_CLUSTERS)
    return [c for c in TOPIC_CLUSTERS if c != key]
