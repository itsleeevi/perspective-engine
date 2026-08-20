"""
Deterministic mock LLM adapter for Phase 1 (local skeleton).

Produces stable, predictable output so tests can assert on control flow
rather than on model responses. No network calls are made.

The mock can be configured to fail quality checks on demand, which lets
tests exercise the retry-cap and escalation paths.
"""

from __future__ import annotations

from adapters.llm.base import (
    LLMAdapter,
    QualityCheckResult,
    ScriptResult,
    ShotBreakdownResult,
    VisualBeatsResult,
)
from graph.script_fixture import fixture_to_beats, to_third_person


class MockLLMAdapter(LLMAdapter):
    """
    Deterministic stand-in for a real LLM provider.

    Parameters
    ----------
    quality_fail_shot_ids:
        Shot ids that should fail the quality check (first ``fail_times``
        times they are checked; after that they pass). Defaults to none.
    fail_times:
        How many consecutive failures to simulate per shot before passing.
        Set to a number > MAX_SHOT_RETRIES to trigger the escalation path.
    """

    def __init__(
        self,
        quality_fail_shot_ids: list[str] | None = None,
        fail_times: int = 1,
    ) -> None:
        self._fail_ids: set[str] = set(quality_fail_shot_ids or [])
        self._fail_times = fail_times
        # Tracks how many times each shot id has been checked so far.
        self._check_counts: dict[str, int] = {}

    async def write_script(
        self,
        topic: str,
        brief: str,
        include_hook: bool = True,
        target_minutes: float = 0.0,
    ) -> ScriptResult:
        # Mirrors the real adapter's fixture-shaped output (hook + named
        # levels), so a mock run exercises the same title-card / chunking
        # code paths a real LLM or fixture run would.
        fixture = {
            "hook": f"Nobody tells you what {topic} really costs.",
            "levels": [
                {
                    "name": "The Beginning",
                    "beats": [
                        f"You start at the bottom of {topic}. It is nothing "
                        "like you imagined it would be.",
                    ],
                },
                {
                    "name": "The Middle",
                    "beats": [
                        "The middle unfolds in unexpected ways. Every choice "
                        "costs you something you didn't expect to lose.",
                    ],
                },
            ],
        }
        return ScriptResult(beats=fixture_to_beats(fixture, include_hook=include_hook))

    async def visualize_beats(
        self, beats: list[str], topic: str = ""
    ) -> VisualBeatsResult:
        """
        Stand in for the real rewrite with the local rule-based one, so mock
        runs produce the same prompt shape a real run would.
        """
        return VisualBeatsResult(
            descriptions=[to_third_person(beat) for beat in beats]
        )

    async def breakdown_shots(
        self, script: list[str], character_descriptor: str
    ) -> ShotBreakdownResult:
        shots = []
        for i, beat in enumerate(script):
            shots.append(
                ShotBreakdownResult.ShotSpec(
                    id=f"shot_{i:03d}",
                    prompt=f"{beat} | {character_descriptor}",
                    duration_seconds=5.0,
                    # First shot is motion to exercise the still-first path;
                    # all others default to static_pan (cheap path).
                    mode="motion" if i == 0 else "static_pan",
                    assigned_model="mock-model-v1",
                )
            )
        return ShotBreakdownResult(shots=shots)

    async def quality_check(
        self,
        shot_id: str,
        clip_url: str,
        still_url: str,
        style_descriptor: str,
        sheet_image_urls: list[str],
    ) -> QualityCheckResult:
        if shot_id not in self._fail_ids:
            return QualityCheckResult(passed=True)

        count = self._check_counts.get(shot_id, 0) + 1
        self._check_counts[shot_id] = count

        if count <= self._fail_times:
            return QualityCheckResult(
                passed=False,
                failure_reason=(
                    f"Mock quality failure #{count} for shot '{shot_id}': "
                    "character drift detected (simulated)."
                ),
            )
        return QualityCheckResult(passed=True)
