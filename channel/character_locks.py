"""Reusable public-figure cartoon locks.

A named person must look like that person as a stick-figure doodle. Historical names stay
out of image prompts and GenerateImage filenames. The lock text plus the
hashed sheet PNG (and optional user photo) are the identity. If a title
names someone already in ``channel/character_locks.json``, reuse that lock
and pass photo then sheet as GenerateImage ``reference_image_paths``.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from channel.paths import ROOT
from channel.schema import Scene, VideoProject

REGISTRY_PATH = ROOT / "channel" / "character_locks.json"
SHEETS_DIR = ROOT / "channel" / "character_sheets"


def _norm(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (name or "").lower()).strip()


def load_registry(path: Path | None = None) -> list[dict[str, Any]]:
    target = path or REGISTRY_PATH
    if not target.is_file():
        return []
    data = json.loads(target.read_text(encoding="utf-8"))
    people = data.get("people") if isinstance(data, dict) else None
    return list(people or [])


def entry_for(historical_name: str, *, registry: list[dict[str, Any]] | None = None) -> dict[str, Any] | None:
    needle = _norm(historical_name)
    if not needle:
        return None
    for entry in registry if registry is not None else load_registry():
        names = [str(entry.get("id") or "")]
        names.extend(str(n) for n in (entry.get("names") or []))
        if any(_norm(n) == needle for n in names if n):
            return entry
    return None


def _rel_file(entry: dict[str, Any], key: str, *, root: Path | None = None) -> Path | None:
    rel = str(entry.get(key) or "").strip()
    if not rel:
        return None
    path = (root or ROOT) / rel
    return path if path.is_file() else None


def sheet_path(entry: dict[str, Any], *, root: Path | None = None) -> Path | None:
    return _rel_file(entry, "sheet", root=root)


def photo_path(entry: dict[str, Any], *, root: Path | None = None) -> Path | None:
    return _rel_file(entry, "photo", root=root)


def asset_rels(entry: dict[str, Any], *, root: Path | None = None) -> list[str]:
    """Repo-relative identity refs: user photo first, then cartoon sheet."""
    base = root or ROOT
    out: list[str] = []
    for key in ("photo", "sheet"):
        path = _rel_file(entry, key, root=base)
        if path is None:
            continue
        try:
            rel = str(path.resolve().relative_to(base.resolve()))
        except ValueError:
            rel = str(path)
        if rel not in out:
            out.append(rel)
    return out


def apply_character_locks(project: VideoProject) -> list[str]:
    """Overwrite matching characters with the shipped cartoon lock."""
    registry = load_registry()
    applied: list[str] = []
    for person in project.characters.values():
        entry = entry_for(person.historical_name, registry=registry)
        if not entry:
            continue
        lock = str(entry.get("visual_lock") or "").strip()
        if lock:
            person.visual_lock = lock
            applied.append(person.id)
    return applied


def _ids_for_shot(
    project: VideoProject,
    scene: Scene | None = None,
    *,
    character_ids: list[str] | None = None,
) -> list[str]:
    if character_ids:
        return list(character_ids)
    if scene is None:
        subject = next((c.id for c in project.characters.values() if c.is_subject), "")
        return [subject] if subject else []
    if scene.who == "empty":
        return []
    ids = list(scene.characters)
    if scene.who == "hero" and not ids:
        subject = next((c.id for c in project.characters.values() if c.is_subject), "")
        if subject:
            ids = [subject]
    return ids


def reference_image_paths(
    project: VideoProject,
    scene: Scene | None = None,
    *,
    character_ids: list[str] | None = None,
    root: Path | None = None,
) -> list[str]:
    """Repo-relative photo then cartoon sheet for locked people in the shot."""
    registry = load_registry()
    seen: set[str] = set()
    rels: list[str] = []
    for cid in _ids_for_shot(project, scene, character_ids=character_ids):
        person = project.characters.get(cid)
        if not person:
            continue
        entry = entry_for(person.historical_name, registry=registry)
        if not entry:
            continue
        for rel in asset_rels(entry, root=root):
            if rel not in seen:
                seen.add(rel)
                rels.append(rel)
    return rels
