"""
Graph-level constants. These values are enforced in code; changing them
requires deliberate review, not just a constant tweak.
"""

# Maximum per-shot quality-gate failures before escalation to human review.
# Reaching this cap routes the shot to human review rather than looping.
MAX_SHOT_RETRIES: int = 3

# Minimum wall-clock seconds between publish calls.
# Enforced inside the publish node regardless of who invokes the graph.
PUBLISH_CADENCE_SECONDS: int = 86_400  # 24 hours

# Directory under the project root where local (Phase 1) assets are written.
LOCAL_ASSETS_DIR: str = "assets"
