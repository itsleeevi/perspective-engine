"""
Content-addressed disk cache for adapter calls (test-time cost control).

Why this exists
---------------
Real provider calls (fal.ai image + video, ElevenLabs, Claude) cost money on
every invocation. During Phase 2 testing a run can crash *after* the expensive
generation steps, and a naive retry re-pays for everything.

The pipeline is deterministic from the topic:
    topic -> script -> shot prompts -> reference sheet -> per-shot stills -> clip
so if we key each provider call by a hash of its inputs and cache the result,
a re-run with the same topic replays every already-completed step for $0 and
only the newly-reached step makes a real (paid) call. The cached assets are
real provider outputs, so the end result is solid, not mocked.

Scope
-----
Disposable, adapters-only. Not imported by anything under ``graph/``.

Controls
--------
- ``ADAPTER_CACHE=0``    disable entirely (always hit the provider).
- ``ADAPTER_CACHE_DIR``  override cache location (default: ``assets/.cache``).

Caveat: cached values may contain provider-hosted URLs (fal.ai) that expire
after some time. For active testing over hours/days this is fine; clear the
cache dir to force fresh generation.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path


def enabled() -> bool:
    """True unless ADAPTER_CACHE=0."""
    return os.environ.get("ADAPTER_CACHE", "1") != "0"


def _root() -> Path:
    raw = Path(os.environ.get("ADAPTER_CACHE_DIR", "assets/.cache"))
    if not raw.is_absolute():
        # Resolve relative to the project root (two levels up from this file).
        raw = Path(__file__).parent.parent / raw
    return raw


def make_key(payload: dict) -> str:
    """Stable sha256 over a JSON-serialised input payload."""
    blob = json.dumps(payload, sort_keys=True, ensure_ascii=True, default=str)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def load(namespace: str, key: str) -> dict | None:
    """Return the cached dict for (namespace, key), or None on miss/disabled."""
    if not enabled():
        return None
    path = _root() / namespace / f"{key}.json"
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return None


def store(namespace: str, key: str, value: dict) -> None:
    """Persist a JSON-able dict for (namespace, key). No-op if disabled."""
    if not enabled():
        return
    path = _root() / namespace / f"{key}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(value))
    tmp.replace(path)  # atomic on POSIX
