"""
Base interface for LLM adapters.

Every concrete implementation (mock, OpenAI, Anthropic, …) must satisfy
this interface. Nodes import and call this interface only; they never
depend on a specific provider.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class ScriptResult:
    """Output of a script-writing call."""

    beats: list[str]
    """Scene beats in order. beats[0] is always the hook."""
    cost_usd: float = 0.0
    """Real provider spend for this call. 0.0 for mocks and cache hits."""


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
    cost_usd: float = 0.0
    """Real provider spend for this call. 0.0 for mocks and cache hits."""


# Shot types that contain no person, so their prompts must not carry the
# hero description (see graph.style.scene_prompt).
CHARACTER_FREE_SHOT_TYPES = frozenset(
    {"extreme close-up", "top-down flatlay", "symbolic graphic"}
)


@dataclass
class VisualBeatsResult:
    """Output of a narration-to-visual-description call."""

    descriptions: list[str]
    """
    One third-person visual scene description per input beat, in the same
    order and of the same length as the input.
    """
    shot_types: list[str] = field(default_factory=list)
    """
    The shot type chosen for each description ("medium shot", "wide shot",
    "extreme close-up", …), parallel to ``descriptions``.

    Kept as a separate field rather than parsed back out of the description
    text because it decides whether the hero description is appended at all,
    and guessing that from prose is exactly the kind of thing that fails
    silently. May be empty (mock adapters, older cache entries), in which
    case callers should assume a character is present.
    """
    cost_usd: float = 0.0
    """Real provider spend for this call. 0.0 for mocks and cache hits."""

    def has_character(self, index: int) -> bool:
        """Whether description ``index`` should carry the hero description."""
        if index >= len(self.shot_types):
            return True
        return self.shot_types[index].strip().lower() not in CHARACTER_FREE_SHOT_TYPES


@dataclass
class QualityCheckResult:
    """Output of a per-shot quality / identity check."""

    passed: bool
    failure_reason: str = ""
    cost_usd: float = 0.0
    """Real provider spend for this call. 0.0 for mocks and cache hits."""


class LLMAdapter(ABC):
    """Abstract LLM adapter shared by all call sites in the graph."""

    @abstractmethod
    async def write_script(
        self,
        topic: str,
        brief: str,
        include_hook: bool = True,
        target_minutes: float = 0.0,
    ) -> ScriptResult:
        """
        Generate a script for the given topic and brief.

        ``include_hook=False`` drops the cold-open hook line so the script
        starts directly on Level One's title card.

        ``target_minutes`` is the intended spoken runtime of the finished
        video; 0.0 leaves the length to the model. Passing it makes the
        writer size the script — level count and words per level — to a word
        budget, rather than writing to an arbitrary length and being cut
        short downstream, which would truncate the story's arc.
        """

    @abstractmethod
    async def breakdown_shots(
        self, script: list[str], character_descriptor: str
    ) -> ShotBreakdownResult:
        """Turn a script into a structured shot list."""

    @abstractmethod
    async def visualize_beats(
        self, beats: list[str], topic: str = ""
    ) -> VisualBeatsResult:
        """
        Turn second-person narration beats into third-person visual scene
        descriptions, one per beat, in order.

        ``topic`` is the video's title. It is what tells the model that an
        unadorned "they ask why you want the job" is a federal background
        interview rather than a retail one, so the props it invents belong to
        the right world.

        Image models read second-person narration ("You sign the papers") as an
        instruction to frame the viewer, and return a camera-facing close-up
        instead of the scene. Rewriting to an observed third-person description
        ("a young man signs papers at a desk in a recruiting office") is what
        produces a wide establishing shot.

        Implementations must return exactly one description per input beat so
        the caller can zip them back to shots.
        """

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
