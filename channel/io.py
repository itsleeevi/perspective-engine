"""Load/save VideoProject JSON."""

from __future__ import annotations

import json
from pathlib import Path

from channel.schema import VideoProject


def load_project(path: Path) -> VideoProject:
    return VideoProject.model_validate_json(path.read_text(encoding="utf-8"))


def save_project(project: VideoProject, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(project.model_dump_json(indent=2) + "\n", encoding="utf-8")
