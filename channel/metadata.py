"""YouTube metadata. Agents may rewrite thumbnail text; this is the floor."""

from __future__ import annotations

import re

from channel.schema import VideoMetadata, VideoProject


def draft_metadata(project: VideoProject) -> VideoMetadata:
    if project.metadata is not None:
        meta = project.metadata
        if not meta.title:
            meta = meta.model_copy(update={"title": project.title})
        if meta.synthetic_content_disclosure is not True:
            meta = meta.model_copy(update={"synthetic_content_disclosure": True})
        return meta

    contradiction = project.story.major_contradiction if project.story else ""
    thumb = _thumbnail_text(contradiction)
    question = project.analysis.core_question
    description = (
        f"{project.title}. {question} "
        "This is an original documentary-style narration with illustrated stills. "
        "Synthetic media: images and voice are generated."
    )
    tags = [
        "what they really think",
        project.analysis.subject.lower(),
        project.analysis.target.lower(),
        "documentary",
        "history",
    ]
    short_title = project.short.short_title if project.short else ""
    chapters = [ch.name for ch in project.story.chapters] if project.story else []
    return VideoMetadata(
        title=project.title,
        description=description.strip(),
        thumbnail_concept=(
            "Two recognizable flat-vector figures or symbols from the story, "
            "high contrast, 2–5 words of thumbnail text, not the full title."
        ),
        thumbnail_text=thumb,
        tags=tags,
        short_title=short_title,
        chapters=chapters,
        synthetic_content_disclosure=True,
    )


def _thumbnail_text(source: str) -> str:
    words = re.findall(r"[A-Za-z']+", source)
    words = [w.upper() for w in words if len(w) > 2][:5]
    if 2 <= len(words) <= 5:
        return " ".join(words)
    return "THE REAL ANSWER"
