"""On-disk layout for one title's working files."""

from __future__ import annotations

from pathlib import Path

from channel.slug import slugify

ROOT = Path(__file__).resolve().parent.parent
PROJECTS = ROOT / "channel" / "projects"


def project_dir(title_or_slug: str) -> Path:
    slug = title_or_slug if re_is_slug(title_or_slug) else slugify(title_or_slug)
    return PROJECTS / slug


def re_is_slug(text: str) -> bool:
    return text == text.lower() and " " not in text and "/" not in text


def _root(root: Path | None) -> Path:
    return root if root is not None else ROOT


def fixture_path(slug: str, root: Path | None = None) -> Path:
    return _root(root) / "fixtures" / f"{slug}.json"


def stills_path(slug: str, root: Path | None = None) -> Path:
    return _root(root) / "fixtures" / f"{slug}_stills.py"


def short_fixture_path(slug: str, root: Path | None = None) -> Path:
    return _root(root) / "fixtures" / f"{slug}_short.json"


def short_stills_path(slug: str, root: Path | None = None) -> Path:
    return _root(root) / "fixtures" / f"{slug}_short_stills.py"


def spec_path(slug: str, root: Path | None = None) -> Path:
    return _root(root) / "fixtures" / "video_specs" / f"{slug}.json"


def jobs_path(prefix: str, root: Path | None = None) -> Path:
    return _root(root) / "fixtures" / f"{prefix}image_jobs.json"
