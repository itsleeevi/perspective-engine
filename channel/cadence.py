"""24-hour assemble cap between different What They Really Think titles.

Same-slug rebuilds (long + Short of one title, or a recut) are allowed.
A new title must wait, unless ``--force``. Empty log allows the first cut.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from channel.paths import ROOT
from graph.config import PUBLISH_CADENCE_SECONDS

# Same 24h number as the LangGraph publish node.
CADENCE_SECONDS = PUBLISH_CADENCE_SECONDS
LOG_NAME = "publish_log.json"


class CadenceError(RuntimeError):
    """Last other title was assembled too recently."""


def log_path(root: Path | None = None) -> Path:
    return (root or ROOT) / "assets" / "youtube" / LOG_NAME


def slug_from_spec(spec: dict[str, Any], *, short: bool = False) -> str:
    raw = ""
    if short:
        raw = str((spec.get("short") or {}).get("fixture") or "")
    if not raw:
        raw = str(spec.get("fixture") or "")
    stem = Path(raw).stem
    if stem.endswith("_short"):
        stem = stem[: -len("_short")]
    return stem


def load_log(root: Path | None = None) -> list[dict[str, Any]]:
    path = log_path(root)
    if not path.is_file():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    return data if isinstance(data, list) else []


def record_assemble(
    slug: str,
    *,
    kind: str = "long",
    root: Path | None = None,
    now: datetime | None = None,
) -> None:
    stamp = now or datetime.now(timezone.utc)
    path = log_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    log = load_log(root)
    log.append({"slug": slug, "kind": kind, "at": stamp.isoformat()})
    path.write_text(json.dumps(log, indent=2) + "\n", encoding="utf-8")


def assert_cadence(
    slug: str,
    *,
    force: bool = False,
    root: Path | None = None,
    now: datetime | None = None,
) -> None:
    if force or not slug:
        return
    clock = now or datetime.now(timezone.utc)
    others = [entry for entry in load_log(root) if entry.get("slug") != slug]
    if not others:
        return
    last = max(others, key=lambda entry: str(entry.get("at") or ""))
    try:
        last_at = datetime.fromisoformat(str(last["at"]))
    except (KeyError, TypeError, ValueError):
        return
    if last_at.tzinfo is None:
        last_at = last_at.replace(tzinfo=timezone.utc)
    elapsed = (clock - last_at).total_seconds()
    if elapsed < CADENCE_SECONDS:
        remaining = CADENCE_SECONDS - elapsed
        other = last.get("slug") or "another title"
        raise CadenceError(
            f"Channel assemble cadence: {other!r} was {elapsed / 3600:.1f}h ago; "
            f"wait {remaining / 3600:.1f}h or pass --force (cap=24h). "
            "Do not ship a new 5–15 minute cut every day from one template."
        )
