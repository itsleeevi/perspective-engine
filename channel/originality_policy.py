"""Permanent originality, anti-repetition, and monetization-safety policy.

These thresholds apply to every new channel title automatically.
Do not restate them in chat — agents read channel/config.py, agent_prompts.py,
and docs/custom-videos.md.
"""

from __future__ import annotations

# --- Originality score (0–100, higher = more original) -----------------------

ORIGINALITY_SCORE_MIN = 80
RECENT_VIDEO_COMPARE_COUNT = 10

# Per-dimension similarity weights when computing the aggregate (must sum to 1).
SIMILARITY_WEIGHTS: dict[str, float] = {
    "hook": 0.15,
    "phrasing": 0.20,
    "structure": 0.15,
    "scene_sequence": 0.15,
    "visual_composition": 0.10,
    "transitions": 0.10,
    "conclusion": 0.10,
    "thumbnail": 0.05,
}

# Similarity above this vs any recent cut fails QA (0–100 scale).
MAX_SINGLE_DIMENSION_SIMILARITY = 85

# --- Monetization readiness (1–10 positive scores; overall 0–100) ------------

BUSINESS_MONETIZATION_THRESHOLDS = {
    "financial_accuracy_min": 8,
    "business_analysis_depth_min": 8,
}

MONETIZATION_THRESHOLDS = {
    "original_research_min": 8,
    "story_originality_min": 8,
    "narration_originality_min": 8,
    "educational_value_min": 8,
    "retention_quality_min": 8,
    "mass_production_risk_max": 3,
    "overall_min": 80,
}

# --- Stock patterns (content repetition, not brand) ----------------------------

BUSINESS_STOCK_HOOKS: tuple[str, ...] = (
    "this company isn't really",
    "this company is not really",
    "isn't really a",
    "is not really a",
)

STOCK_HOOK_OPENERS: tuple[str, ...] = (
    "is remembered as",
    "when it came to",
    "throughout his life",
    "throughout her life",
    "when people think of",
    "most people assume",
)

STOCK_TRANSITIONS: tuple[str, ...] = (
    "but that wasn't the whole story",
    "but that was not the whole story",
    "then everything changed",
    "but the story does not end there",
    "but behind the public image",
    "but there was more to it",
    "and that is only half the story",
)

STOCK_ENDINGS: tuple[str, ...] = (
    "only half the story",
    "is only half the story",
    "but that opinion was only half",
    "the rest is for another video",
)

GENERIC_AI_PHRASES: tuple[str, ...] = (
    "it is important to note",
    "furthermore",
    "consequently",
    "nevertheless",
    "from a geopolitical perspective",
    "this complex relationship demonstrates",
    "it can therefore be concluded",
    "throughout history",
    "in conclusion",
    "to summarize",
)

# Overused visual beats when they dominate a storyboard without historical reason.
GENERIC_SCENE_PATTERNS: tuple[str, ...] = (
    "person sitting at desk",
    "sitting at desk",
    "pointing at map",
    "looking at newspaper",
    "signing paper",
    "person at desk",
    "desk lamp only",
)

# Hook styles agents may choose from (guidance, not a template).
HOOK_STYLES: tuple[str, ...] = (
    "CONTRADICTION",
    "SHOCKING_ACTION",
    "VERIFIED_QUOTE",
    "EVENT",
    "MYSTERY",
    "REVERSAL",
)

# Ending strategies agents may choose from.
ENDING_STRATEGIES: tuple[str, ...] = (
    "REVERSE_PERSPECTIVE",
    "CONSEQUENCE",
    "LEGACY",
    "FINAL_QUOTE",
    "OPEN_QUESTION",
    "RELATED_PERSON",
)

# Story archetypes (research picks the shape — do not force one sequence).
STORY_ARCHETYPES: tuple[str, ...] = (
    "RIVALRY",
    "FRIENDSHIP_TO_RIVALRY",
    "ALLIANCE_TO_BETRAYAL",
    "ADMIRATION_TO_DISAPPOINTMENT",
    "RELUCTANT_RESPECT",
    "IDEOLOGICAL_EVOLUTION",
    "RELIGIOUS_EVOLUTION",
    "POLITICAL_WORLDVIEW",
    "COUNTRY_WORLDVIEW",
    "COMPETITOR_RELATIONSHIP",
    "MENTOR_STUDENT",
    "LOVE_HATE_RELATIONSHIP",
    "MISUNDERSTOOD_OPINION",
    "FEAR_AND_RESPECT",
    "PUBLIC_POSITION_VS_PRIVATE_POSITION",
)

# Research source priority (for agent prompts and QA notes).
BUSINESS_SOURCE_PRIORITY: tuple[str, ...] = (
    "company annual reports",
    "SEC or equivalent filings",
    "investor presentations",
    "earnings calls",
    "official company statistics",
    "shareholder letters",
    "regulatory documents",
    "credible financial publications",
    "reputable business journalism",
    "respected industry research",
    "founder or executive interviews",
    "books that explain a decision",
)

RESEARCH_SOURCE_PRIORITY: tuple[str, ...] = (
    "primary sources",
    "speeches",
    "interviews",
    "letters",
    "diaries",
    "official documents",
    "memoirs",
    "reputable biographies",
    "academic sources",
    "reputable historical references",
)

# Brand elements similarity checks IGNORE (channel format may repeat).
BRAND_IGNORE_PATTERNS: tuple[str, ...] = (
    "what they really think",
    "behind the business",
    "simple flat 2d",
    "kokoro",
    "illustrated documentary",
    "stills and narration are generated",
)
