"""Filesystem-safe slug from a title. No person-specific rules."""

from __future__ import annotations

import re


def slugify(text: str, max_len: int = 48) -> str:
    s = text.lower().strip()
    if re.search(r"\s+really\s+(thought|thinks)\s+about\s+", s):
        s = re.sub(r"^what\s+", "", s)
        s = re.sub(r"\s+really\s+(thought|thinks)\s+about\s+", "-", s)
    else:
        s = re.sub(r"^how\s+", "", s)
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s[:max_len].rstrip("-") or "untitled"


def character_id(display_name: str, era: str = "") -> str:
    base = re.sub(r"[^a-z0-9]+", "_", display_name.lower()).strip("_")
    era_part = re.sub(r"[^a-z0-9]+", "_", era.lower()).strip("_")
    return f"{base}_{era_part}" if era_part else base
