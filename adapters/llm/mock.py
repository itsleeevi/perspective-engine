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
)


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

    async def write_script(self, topic: str, brief: str) -> ScriptResult:
        return ScriptResult(
            beats=[
                f"[HOOK] The world has never seen {topic} from this angle.",
                f"We begin at the very start of {topic}.",
                "The middle unfolds in unexpected ways.",
                "A turn that reframes everything before it.",
                "The perspective completes its shift.",
            ]
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
