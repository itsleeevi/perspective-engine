"""
publish node — mock publish with hard-coded cadence cap.

Invariants enforced here:
    - ``metadata.synthetic_content_disclosure`` must be True.
    - Publish may not be called more than once per PUBLISH_CADENCE_SECONDS.
      The last-publish timestamp is stored in ``state.last_published_at`` so
      the cap is testable without external state (just inject a clock).
"""

from __future__ import annotations

from datetime import datetime, timezone

from graph.config import PUBLISH_CADENCE_SECONDS
from graph.state import PipelineState


async def publish(
    state: PipelineState,
    _now: datetime | None = None,
) -> dict:
    """
    Mock publish step.

    Parameters
    ----------
    _now:
        Injectable clock for testing the cadence cap.  Defaults to
        ``datetime.now(timezone.utc)``.

    Returns a partial state update: ``last_published_at``.
    """
    # Invariant: disclosure flag must be set before publish.
    if not state.metadata.synthetic_content_disclosure:
        raise ValueError(
            "Invariant violated: metadata.synthetic_content_disclosure must be "
            "True before publish. Call generate_metadata first."
        )

    now = _now or datetime.now(timezone.utc)

    # Cadence cap: reject if last publish was too recent.
    if state.last_published_at:
        try:
            last = datetime.fromisoformat(state.last_published_at)
            # Make last timezone-aware if necessary for comparison.
            if last.tzinfo is None:
                last = last.replace(tzinfo=timezone.utc)
            elapsed = (now - last).total_seconds()
            if elapsed < PUBLISH_CADENCE_SECONDS:
                remaining = PUBLISH_CADENCE_SECONDS - elapsed
                raise ValueError(
                    f"Publish cadence cap: last published {elapsed:.0f}s ago; "
                    f"must wait {remaining:.0f}s more "
                    f"(cap={PUBLISH_CADENCE_SECONDS}s)."
                )
        except (ValueError, TypeError) as exc:
            # Re-raise cadence violations; ignore malformed timestamp.
            if "cadence cap" in str(exc):
                raise

    # Phase 1: mock — record the timestamp only.
    return {"last_published_at": now.isoformat()}
