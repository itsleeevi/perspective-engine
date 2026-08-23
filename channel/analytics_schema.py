"""Future YouTube analytics hook. No live API is wired yet."""

from __future__ import annotations

from pydantic import BaseModel, Field


class PerformanceRecord(BaseModel):
    """Stored after a cut is live so topic selection can learn later."""

    slug: str
    channel_mode: str
    title: str = ""
    impressions: int | None = None
    ctr: float | None = None
    views: int | None = None
    average_view_duration: float | None = None
    average_percentage_viewed: float | None = None
    watch_hours: float | None = None
    subscribers_gained: int | None = None
    traffic_sources: dict[str, float] = Field(default_factory=dict)
    retention_curve: list[float] = Field(default_factory=list)
    rpm: float | None = None
    industry: str = ""
    title_pattern: str = ""
    thumbnail_concept: str = ""
    duration_seconds: float | None = None
    story_archetype: str = ""
