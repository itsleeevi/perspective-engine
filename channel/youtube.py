"""YouTube pack: description, tags, thumbnail job, 1280×720 JPEG overlay.

Compile writes the job + draft copy. After assemble, ``python -m channel youtube
<slug>`` (also called from ``run_custom_video``) stamps real chapter times.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from channel.config import (
    CHANNEL,
    CHANNEL_ABOUT,
    HOST_ATTRIBUTION,
    YOUTUBE_DISCLOSURE,
    visual_accent_for,
)
from channel.paths import ROOT, jobs_path, spec_path
from channel.prompts import strip_character_names
from channel.schema import VideoProject

THUMB_W, THUMB_H = 1280, 720
# Paste the long-cut URL after upload. Agents replace VIDEO_ID (or set
# youtube.full_video_url on the spec) and re-run ``python -m channel youtube``.
DEFAULT_FULL_VIDEO_URL = "https://youtu.be/VIDEO_ID"


def youtube_stem(slug: str) -> str:
    return slug.replace("-", "_")


def youtube_dir(root: Path | None = None) -> Path:
    return (root or ROOT) / "assets" / "youtube"


def timestamp(seconds: float) -> str:
    total = max(0, int(round(seconds)))
    hours, remainder = divmod(total, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


def chapter_lines(chapters: list[dict[str, Any]] | None) -> list[str]:
    """YouTube chapters. First line must be 0:00."""
    lines: list[str] = []
    if chapters:
        for ch in chapters:
            label = str(ch.get("label") or "").strip().rstrip(":")
            start = float(ch.get("start_seconds") or 0.0)
            if label:
                lines.append(f"{timestamp(start)} {label}")
    if lines and not lines[0].startswith("0:00"):
        lines.insert(0, "0:00 Intro")
    return lines


def _strip_stale_footer(body: str) -> str:
    """Drop chapter stamps and old disclosure so we can rewrite them."""
    body = re.split(r"\n(?=\d+:\d{2}\b)", body, maxsplit=1)[0].strip()
    previous = None
    while previous != body:
        previous = body
        body = re.sub(
            r"\n+Synthetic media:.*$", "", body, flags=re.I | re.S
        ).strip()
        body = re.sub(
            r"\n+Researched and written for What They Really Think.*$",
            "",
            body,
            flags=re.I | re.S,
        ).strip()
        body = re.sub(
            r"\n+Illustrated documentary\..*$",
            "",
            body,
            flags=re.I | re.S,
        ).strip()
    return body


def description_footer() -> str:
    return f"{HOST_ATTRIBUTION}\n\n{YOUTUBE_DISCLOSURE}"


def long_description(youtube: dict[str, Any], chapters: list[str]) -> str:
    body = _strip_stale_footer((youtube.get("description") or "").strip())
    parts = [body] if body else [str(youtube.get("title") or CHANNEL.name)]
    if chapters:
        parts.append("\n".join(chapters))
    parts.append(description_footer())
    return "\n\n".join(parts).strip() + "\n"


def full_video_url(youtube: dict[str, Any]) -> str:
    raw = (youtube.get("full_video_url") or "").strip()
    return raw or DEFAULT_FULL_VIDEO_URL


def short_summary(youtube: dict[str, Any]) -> str:
    title = (youtube.get("short_title") or youtube.get("title") or "").strip()
    paras = [
        p.strip()
        for p in (youtube.get("description") or "").split("\n\n")
        if p.strip()
    ]
    hook = paras[1] if len(paras) > 1 else (paras[0] if paras else title)
    hook = hook.split("\n")[0].strip()
    if len(hook) > 220:
        hook = hook[:217].rsplit(" ", 1)[0] + "…"
    if title and hook.lower().startswith(title.lower()):
        return hook
    if title and hook:
        return f"{title}. {hook}"
    return title or hook


def short_description(youtube: dict[str, Any]) -> str:
    """YouTube Shorts description: long-cut link first, then punch + disclosure."""
    return (
        f"Watch the full video:\n{full_video_url(youtube)}\n\n"
        f"{short_summary(youtube)}\n\n"
        f"{YOUTUBE_DISCLOSURE}\n"
    )


def tags_line(tags: list[str]) -> str:
    seen: set[str] = set()
    out: list[str] = []
    budget = 500
    used = 0
    for raw in tags:
        tag = " ".join(raw.split()).strip().strip(",")
        if not tag:
            continue
        key = tag.lower()
        if key in seen:
            continue
        extra = len(tag) + (2 if out else 0)
        if used + extra > budget:
            break
        seen.add(key)
        out.append(tag)
        used += extra
    return ", ".join(out) + "\n"


def thumbnail_prompt(project: VideoProject) -> str:
    from channel.bibles import visual_lock

    meta = project.metadata
    concept = (meta.thumbnail_concept if meta else "") or (
        "Tight chest-up of the subject. Face fills at least 30 percent of the "
        "frame, well-lit, subtle natural expression. Empty right third for type."
    )
    subject = next((c for c in project.characters.values() if c.is_subject), None)
    lock = visual_lock(subject) if subject else ""
    prop = ""
    if project.story and project.story.signature_prop:
        prop = f" Signature object: {project.story.signature_prop}."
    assembled = " ".join(
        p
        for p in (
            CHANNEL.visual_style,
            visual_accent_for(project.slug),
            "Horizontal 16:9 YouTube thumbnail. TIGHT crop, chest-up or closer. "
            "The subject's FACE fills at least 30 percent of the frame and is "
            "the brightest thing in the picture. Dramatic single-source light, "
            "bold colour contrast, clean simple backdrop. Subtle natural "
            "expression, not a grimace, not a shout. Empty right third of the "
            "frame for type added later. No tiny figures, no wide establishing "
            "shot, no clutter.",
            CHANNEL.negative_style,
            "NO readable text, NO letters, NO captions, NO title card, "
            "NO watermark. Type will be added later.",
            lock,
            concept,
            prop,
        )
        if p
    )
    return strip_character_names(assembled, project)


def write_thumbnail_job(project: VideoProject, *, root: Path | None = None) -> Path:
    slug = project.slug
    stem = youtube_stem(slug)
    meta = project.metadata
    text = (meta.thumbnail_text if meta else "") or "THE REAL ANSWER"
    job = {
        "id": "thumb",
        "filename": f"{slug}_thumbnail.png",
        "aspect": "16:9",
        "overlay_text": text,
        "output_jpeg": f"assets/youtube/{stem}_thumbnail_1280x720.jpg",
        "prompt": thumbnail_prompt(project),
    }
    out = jobs_path(f"{slug}_thumbnail_", root)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"jobs": [job]}, indent=2) + "\n", encoding="utf-8")
    return out


def write_pack(
    spec: dict[str, Any],
    *,
    assemble: dict[str, Any] | None = None,
    root: Path | None = None,
) -> dict[str, str]:
    """Write paste-ready YouTube files under assets/youtube/."""
    base = root or ROOT
    youtube = dict(spec.get("youtube") or {})
    topic = spec.get("topic") or youtube.get("title") or ""
    slug = Path(spec.get("fixture") or "video.json").stem
    stem = youtube_stem(slug)
    chapters = chapter_lines((assemble or {}).get("chapters"))
    dest = youtube_dir(base)
    dest.mkdir(parents=True, exist_ok=True)

    tags = list(youtube.get("tags") or [])
    if not tags:
        tags = [CHANNEL.name.lower()]

    long_path = dest / f"{stem}_description.txt"
    short_path = dest / f"{stem}_short_description.txt"
    tags_path = dest / f"{stem}_tags.txt"
    about_path = dest / "channel_about.txt"
    long_path.write_text(long_description(youtube, chapters), encoding="utf-8")
    short_path.write_text(short_description(youtube), encoding="utf-8")
    tags_path.write_text(tags_line(tags), encoding="utf-8")
    about_path.write_text(CHANNEL_ABOUT, encoding="utf-8")

    written = {
        "description": str(long_path),
        "short_description": str(short_path),
        "tags": str(tags_path),
        "about": str(about_path),
        "title": str(youtube.get("title") or topic),
        "short_title": str(youtube.get("short_title") or ""),
        "thumbnail_text": str(youtube.get("thumbnail_text") or ""),
    }
    return written


def load_assemble_manifest(spec: dict[str, Any], *, root: Path | None = None) -> dict[str, Any] | None:
    base = root or ROOT
    topic = spec.get("topic") or ""
    safe = re.sub(r"[^a-z0-9]+", "_", topic.lower()).strip("_")[:40]
    path = base / "assets" / "output" / f"{safe}_final.json"
    if path.is_file():
        return json.loads(path.read_text(encoding="utf-8"))
    return None


def find_thumbnail_still(slug: str, *, root: Path | None = None) -> Path | None:
    """Locate a text-free thumbnail still (GenerateImage output)."""
    base = root or ROOT
    names = (f"{slug}_thumbnail.png", f"{slug}_thumb.png")
    cursor = (
        Path.home()
        / ".cursor"
        / "projects"
        / str(base).strip("/").replace("/", "-")
        / "assets"
    )
    dirs = (
        base / "assets" / "grok_thumbs",
        base / "assets" / "youtube",
        cursor,
    )
    for folder in dirs:
        for name in names:
            path = folder / name
            if path.is_file():
                return path
    return None


def write_pack_for_slug(slug: str, *, root: Path | None = None) -> dict[str, str]:
    spec = json.loads(spec_path(slug, root).read_text(encoding="utf-8"))
    assemble = load_assemble_manifest(spec, root=root)
    return write_pack(spec, assemble=assemble, root=root)
