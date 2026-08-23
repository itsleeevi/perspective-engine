"""Shared types for one What They Really Think video. No person is hardcoded."""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class SubjectStatus(str, Enum):
    deceased = "deceased"
    living = "living"
    unknown = "unknown"
    not_a_person = "not_a_person"


class EvidenceKind(str, Enum):
    said = "said"
    wrote = "wrote"
    action_suggests = "action_suggests"
    historian_interprets = "historian_interprets"
    unknown_private = "unknown_private"


class EvidenceFlag(str, Enum):
    surprising = "SURPRISING"
    contradictory = "CONTRADICTORY"
    visual = "VISUAL"
    emotional = "EMOTIONAL"
    important = "IMPORTANT"
    context_only = "CONTEXT_ONLY"


class StoryArchetype(str, Enum):
    rivalry = "RIVALRY"
    friendship_to_rivalry = "FRIENDSHIP_TO_RIVALRY"
    alliance_to_betrayal = "ALLIANCE_TO_BETRAYAL"
    admiration = "ADMIRATION"
    admiration_to_disappointment = "ADMIRATION_TO_DISAPPOINTMENT"
    reluctant_respect = "RELUCTANT_RESPECT"
    hatred = "HATRED"
    complicated_respect = "COMPLICATED_RESPECT"
    ideological_evolution = "IDEOLOGICAL_EVOLUTION"
    religious_evolution = "RELIGIOUS_EVOLUTION"
    friendship_to_conflict = "FRIENDSHIP_TO_CONFLICT"
    country_worldview = "COUNTRY_WORLDVIEW"
    religious_belief = "RELIGIOUS_BELIEF"
    political_worldview = "POLITICAL_WORLDVIEW"
    competitor_relationship = "COMPETITOR_RELATIONSHIP"
    mentor_student = "MENTOR_STUDENT"
    love_hate_relationship = "LOVE_HATE_RELATIONSHIP"
    misunderstood_opinion = "MISUNDERSTOOD_OPINION"
    fear_and_respect = "FEAR_AND_RESPECT"
    public_vs_private = "PUBLIC_POSITION_VS_PRIVATE_POSITION"
    unknown = "UNKNOWN"


class ScenePurpose(str, Enum):
    hook = "hook"
    context = "context"
    question = "question"
    answer = "answer"
    evidence = "evidence"
    escalation = "escalation"
    reveal = "reveal"
    contradiction = "contradiction"
    transition = "transition"
    resolution = "resolution"
    next_video_bridge = "next_video_bridge"


class TitleAnalysis(BaseModel):
    title: str
    subject: str
    target: str
    verb: Literal["Thought", "Thinks"]
    subject_status: SubjectStatus = SubjectStatus.unknown
    category: str = "unknown"
    relationship_type: str = "unknown until researched"
    time_period: str = "unknown until researched"
    core_question: str
    research_priority: str = "high"
    quotes_need_primary_sources: bool = True
    target_kind: str = "unknown"
    special_instructions: str = ""
    target_duration_seconds: int | None = None


class SourceRef(BaseModel):
    title: str
    url: str = ""
    kind: str = "reference"
    source_type: str = ""
    year: str = ""
    note: str = ""


class Claim(BaseModel):
    claim_id: str
    claim: str
    kind: EvidenceKind
    sources: list[SourceRef] = Field(default_factory=list)
    confidence: Literal["high", "medium", "low", "disputed"] = "medium"
    flags: list[EvidenceFlag] = Field(default_factory=list)
    quote: str = ""
    date: str = ""
    is_direct_quote: bool = False


class ResearchPack(BaseModel):
    subject: str
    target: str
    summary: str = ""
    claims: list[Claim] = Field(default_factory=list)
    contradictions: list[str] = Field(default_factory=list)
    timeline: list[str] = Field(default_factory=list)
    visual_opportunities: list[str] = Field(default_factory=list)
    insufficient_evidence: bool = False
    insufficient_note: str = ""
    seed_sources: list[SourceRef] = Field(default_factory=list)


class FactCheckReport(BaseModel):
    ok: bool
    flags: list[str] = Field(default_factory=list)
    rejected_claim_ids: list[str] = Field(default_factory=list)


class Chapter(BaseModel):
    name: str
    purpose: ScenePurpose
    narration: str


class StoryPlan(BaseModel):
    hook: str
    central_question: str
    initial_assumption: str
    first_reveal: str
    major_contradiction: str
    turning_point: str
    final_answer: str
    title_payoff: str
    next_video_bridge: str
    archetype: StoryArchetype = StoryArchetype.unknown
    hook_style: str = ""
    ending_strategy: str = ""
    signature_prop: str = ""
    chapters: list[Chapter] = Field(default_factory=list)


class Character(BaseModel):
    id: str
    display_name: str
    historical_name: str = ""
    era: str = ""
    age_range: str = ""
    face: str = ""
    hair: str = ""
    facial_hair: str = ""
    body: str = ""
    default_clothing: str = ""
    palette: list[str] = Field(default_factory=list)
    recognition_features: list[str] = Field(default_factory=list)
    is_subject: bool = False
    visual_lock: str = ""


class Location(BaseModel):
    id: str
    description: str
    palette: list[str] = Field(default_factory=list)


class Scene(BaseModel):
    scene_id: str
    narration: str
    purpose: ScenePurpose
    visual_type: str = "character"
    characters: list[str] = Field(default_factory=list)
    location: str = ""
    action: str
    composition: str = "medium shot"
    camera_motion: str = "slow push-in"
    on_screen_text: str | None = None
    source_claim_ids: list[str] = Field(default_factory=list)
    who: str = "hero"


class QaScores(BaseModel):
    hook: int = 0
    curiosity: int = 0
    pacing: int = 0
    clarity: int = 0
    story: int = 0
    contradiction: int = 0
    visual_potential: int = 0
    emotional_variety: int = 0
    title_payoff: int = 0
    ending: int = 0
    notes: list[str] = Field(default_factory=list)

    def critical_below(self, threshold: int) -> list[str]:
        fields = (
            "hook",
            "curiosity",
            "pacing",
            "clarity",
            "story",
            "contradiction",
            "visual_potential",
            "emotional_variety",
            "title_payoff",
            "ending",
        )
        return [name for name in fields if getattr(self, name) < threshold]


class SimilarityBreakdown(BaseModel):
    compared_slug: str
    hook: float = 0.0
    phrasing: float = 0.0
    structure: float = 0.0
    scene_sequence: float = 0.0
    visual_composition: float = 0.0
    transitions: float = 0.0
    conclusion: float = 0.0
    thumbnail: float = 0.0

    def weighted(self) -> float:
        from channel.originality_policy import SIMILARITY_WEIGHTS

        parts = {
            "hook": self.hook,
            "phrasing": self.phrasing,
            "structure": self.structure,
            "scene_sequence": self.scene_sequence,
            "visual_composition": self.visual_composition,
            "transitions": self.transitions,
            "conclusion": self.conclusion,
            "thumbnail": self.thumbnail,
        }
        return sum(parts[k] * SIMILARITY_WEIGHTS[k] for k in SIMILARITY_WEIGHTS)


class OriginalityReport(BaseModel):
    slug: str
    originality_score: float = 100.0
    mass_production_similarity: float = 0.0
    comparisons: list[SimilarityBreakdown] = Field(default_factory=list)
    flags: list[str] = Field(default_factory=list)
    ready_for_images: bool = True


class MonetizationReadiness(BaseModel):
    original_research: int = 0
    story_originality: int = 0
    narration_originality: int = 0
    visual_originality: int = 0
    educational_value: int = 0
    source_quality: int = 0
    character_consistency: int = 0
    retention_quality: int = 0
    mass_production_risk: int = 1
    overall: int = 0
    ready_to_publish: bool = False
    originality_score: float = 100.0
    notes: list[str] = Field(default_factory=list)


class ShortPlan(BaseModel):
    short_title: str
    short_narration: str
    long_video_connection: str
    recommended_related_video: bool = True
    scenes: list[Scene] = Field(default_factory=list)


class VideoMetadata(BaseModel):
    title: str
    description: str
    thumbnail_concept: str = ""
    thumbnail_text: str = ""
    tags: list[str] = Field(default_factory=list)
    short_title: str = ""
    chapters: list[str] = Field(default_factory=list)
    synthetic_content_disclosure: bool = True


class VideoProject(BaseModel):
    """Shared context for every agent on one title."""

    title: str
    slug: str
    analysis: TitleAnalysis
    research: ResearchPack = Field(default_factory=lambda: ResearchPack(subject="", target=""))
    factcheck: FactCheckReport = Field(default_factory=lambda: FactCheckReport(ok=False))
    story: StoryPlan | None = None
    characters: dict[str, Character] = Field(default_factory=dict)
    locations: dict[str, Location] = Field(default_factory=dict)
    scenes: list[Scene] = Field(default_factory=list)
    qa: QaScores | None = None
    originality: OriginalityReport | None = None
    monetization: MonetizationReadiness | None = None
    short: ShortPlan | None = None
    metadata: VideoMetadata | None = None
    special_instructions: str = ""
