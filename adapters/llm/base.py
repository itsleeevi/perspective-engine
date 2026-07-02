"""
Base interface for LLM adapters.

Every concrete implementation (mock, OpenAI, Anthropic, …) must satisfy
this interface. Nodes import and call this interface only; they never
depend on a specific provider.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class ScriptResult:
    """Output of a script-writing call."""

    beats: list[str]
    """Scene beats in order. beats[0] is always the hook."""


@dataclass
class ShotBreakdownResult:
    """Output of a shot-breakdown call."""

    @dataclass
    class ShotSpec:
        id: str
        prompt: str
        duration_seconds: float
        mode: str        # "motion" | "static_pan"
        assigned_model: str

    shots: list[ShotSpec]


@dataclass
class QualityCheckResult:
    """Output of a per-shot quality / identity check."""

    passed: bool
    failure_reason: str = ""


class LLMAdapter(ABC):
    """Abstract LLM adapter shared by all call sites in the graph."""

    @abstractmethod
    async def write_script(self, topic: str, brief: str) -> ScriptResult:
        """Generate a script for the given topic and brief."""

    @abstractmethod
    async def breakdown_shots(
        self, script: list[str], character_descriptor: str
    ) -> ShotBreakdownResult:
        """Turn a script into a structured shot list."""

    @abstractmethod
    async def quality_check(
        self,
        shot_id: str,
        clip_url: str,
        still_url: str,
        style_descriptor: str,
        sheet_image_urls: list[str],
    ) -> QualityCheckResult:
        """
        Check technical quality and character identity for a generated clip.

        The implementation should compare the clip against the reference sheet
        and style descriptor, returning passed=False with a failure_reason
        whenever the character drifts or technical quality is unacceptable.
        """
