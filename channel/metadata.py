"""YouTube metadata. Agents may rewrite thumbnail text; this is the floor."""

from __future__ import annotations

import re

from channel.config import config_for_project
from channel.modes import is_business
from channel.schema import VideoMetadata, VideoProject


def draft_metadata(project: VideoProject) -> VideoMetadata:
    existing = project.metadata
    payoff = (project.story.title_payoff if project.story else "").strip()
    hook = (project.story.hook if project.story else "").strip()
    contradiction = (project.story.major_contradiction if project.story else "").strip()
    question = project.analysis.core_question
    title = project.title

    lead = f"{title}: {payoff}" if payoff else f"{title}. {question}"
    extra = _first_sentences(hook, 2)
    if extra and extra.lower() not in lead.lower():
        body = f"{lead}\n\n{extra}"
    else:
        body = lead
    if contradiction and contradiction.lower() not in body.lower():
        body = f"{body}\n\n{contradiction}"
    cfg = config_for_project(project)
    body = (
        f"{body}\n\n"
        f"This is an illustrated documentary from {cfg.name}."
    )
    if is_business(project.channel_mode):
        body = f"{body}\n\nEducational analysis of a business model. Not investment advice."
        sources = _source_lines(project)
        if sources:
            body = f"{body}\n\nSources / further reading:\n" + "\n".join(sources)
        if project.story and project.story.next_video_bridge.strip():
            body = f"{body}\n\nRelated: {project.story.next_video_bridge.strip()}"

    tags = _default_tags(project)
    thumb = (existing.thumbnail_text if existing else "") or (
        "THE REAL ENGINE" if is_business(project.channel_mode) else "THE REAL ANSWER"
    )
    if existing and existing.thumbnail_concept:
        concept = existing.thumbnail_concept
    elif is_business(project.channel_mode):
        concept = (
            "One simplified company environment or product plus one business "
            "symbol (membership card, network, store, app). High contrast, "
            "clean backdrop. Empty right third for 2–5 words of type added "
            "later. Not a historical portrait. Not the full title."
        )
    else:
        concept = (
            "Tight chest-up of the subject. Face fills at least 30 percent of the "
            "frame, well-lit from one side, subtle expression. Signature object "
            "small. Empty right third for 2–5 words of type added later. Not the "
            "full title."
        )
    if existing and existing.description.strip() and len(existing.description) > 160:
        body = existing.description.strip()
    if existing and existing.tags:
        tags = list(dict.fromkeys([*existing.tags, *tags]))

    short_title = ""
    if project.short and project.short.short_title:
        short_title = project.short.short_title
    elif existing:
        short_title = existing.short_title
    chapters = [ch.name for ch in project.story.chapters] if project.story else []
    return VideoMetadata(
        title=title,
        description=body.strip(),
        thumbnail_concept=concept,
        thumbnail_text=thumb,
        tags=tags,
        short_title=short_title,
        chapters=chapters or (existing.chapters if existing else []),
        synthetic_content_disclosure=True,
    )


def _source_lines(project: VideoProject) -> list[str]:
    seen: set[str] = set()
    lines: list[str] = []
    refs = list(project.research.seed_sources)
    for claim in project.research.claims:
        refs.extend(claim.sources)
    for ref in refs:
        title = " ".join((ref.title or "").split())
        if not title or title.lower() in seen:
            continue
        seen.add(title.lower())
        year = f" ({ref.year})" if ref.year else ""
        lines.append(f"- {title}{year}")
        if len(lines) >= 8:
            break
    return lines


def _first_sentences(text: str, n: int) -> str:
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return " ".join(p for p in parts[:n] if p).strip()


def _default_tags(project: VideoProject) -> list[str]:
    cfg = config_for_project(project)
    subject = project.analysis.subject.strip()
    target = project.analysis.target.strip()
    tags = [
        cfg.name.lower(),
        subject.lower(),
        target.lower(),
        f"{subject} {target}".lower(),
        project.title.lower(),
        "illustrated documentary",
    ]
    if is_business(project.channel_mode):
        tags.extend(
            [
                "business documentary",
                "behind the business",
                "business model",
            ]
        )
    else:
        tags.extend(
            [
                "history documentary",
                "what they really thought",
            ]
        )
    if project.story and project.story.signature_prop:
        tags.append(project.story.signature_prop.lower())
    out: list[str] = []
    seen: set[str] = set()
    for tag in tags:
        tag = " ".join(tag.split())
        if tag and tag not in seen:
            seen.add(tag)
            out.append(tag)
    return out
