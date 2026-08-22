"""CLI: title in → project files out.

    .venv/bin/python -m channel init "What Einstein Really Thought About Religion"

Subcommands:
    init           parse title, seed research, write project skeleton
    analyze        parse a title and print JSON (no files)
    research-seed  re-fetch the encyclopedia seed into an existing project
    chunks         print narration chunks (needs a story)
    compile        write fixtures / stills / spec / image jobs
    qa             run mechanical retention checks
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from channel.compile import chunk_list, compile_project
from channel.config import CHANNEL
from channel.factcheck import factcheck
from channel.io import load_project, save_project
from channel.paths import ROOT, project_dir, spec_path
from channel.qa import mechanical_qa, narration_of, word_count
from channel.research import seed_research
from channel.schema import ResearchPack, VideoProject
from channel.slug import slugify
from channel.title import analyze_title


def _init(args: argparse.Namespace) -> int:
    analysis = analyze_title(
        args.title,
        special_instructions=args.instructions or "",
        target_duration_seconds=args.duration,
    )
    slug = slugify(analysis.title)
    d = project_dir(slug)
    d.mkdir(parents=True, exist_ok=True)
    pack = ResearchPack(subject=analysis.subject, target=analysis.target)
    if not args.skip_seed:
        pack = seed_research(analysis)
    project = VideoProject(
        title=analysis.title,
        slug=slug,
        analysis=analysis,
        research=pack,
        special_instructions=analysis.special_instructions,
    )
    save_project(project, d / "project.json")
    (d / "README.md").write_text(
        _agent_readme(slug, analysis.title),
        encoding="utf-8",
    )
    print(f"project: {d / 'project.json'}")
    print(f"subject={analysis.subject!r} target={analysis.target!r} verb={analysis.verb}")
    print(f"core_question: {analysis.core_question}")
    print(f"research seed sources: {len(pack.seed_sources)}")
    print("Next: fill claims in research, then story/characters/scenes. See the README.")
    return 0


def _analyze(args: argparse.Namespace) -> int:
    analysis = analyze_title(
        args.title,
        special_instructions=args.instructions or "",
        target_duration_seconds=args.duration,
    )
    print(analysis.model_dump_json(indent=2))
    return 0


def _research_seed(args: argparse.Namespace) -> int:
    path, project = _load(args.slug)
    project.research = seed_research(project.analysis)
    save_project(project, path)
    print(f"seed sources: {len(project.research.seed_sources)}")
    return 0


def _agent_readme(slug: str, title: str) -> str:
    from channel import agent_prompts

    return f"""# {title}

Working directory for this video. Story content lives in `project.json`.
Style, voice, and QA rules live in `channel/config.py` — do not copy a person into that file.

## Pipeline

1. Researcher — {agent_prompts.RESEARCHER.strip().splitlines()[0]}
2. Fact check — `python -m channel qa {slug}` after claims exist
3. Story architect, bibles, narration (650–750 words)
4. `python -m channel chunks {slug}`
5. Scene breakdown, 1:1 with chunks
6. `python -m channel compile {slug}`
7. GenerateImage each job in `fixtures/{slug}_v1_image_jobs.json` (Cursor Grok)
8. `.venv/bin/python scripts/run_short.py fixtures/video_specs/{slug}.json`
9. `.venv/bin/python scripts/run_custom_video.py fixtures/video_specs/{slug}.json`
10. Update `docs/videos/{slug}.md`

Voice is Kokoro `{CHANNEL.kokoro_voice}` (free). Never Edge. Never ElevenLabs.
Images are Cursor Grok GenerateImage. Do not invent quotes.
"""


def _load(slug: str) -> tuple[Path, VideoProject]:
    path = project_dir(slug) / "project.json"
    if not path.is_file():
        raise SystemExit(f"no project at {path} — run: python -m channel init \"<title>\"")
    return path, load_project(path)


def _chunks(args: argparse.Namespace) -> int:
    _path, project = _load(args.slug)
    if not project.story:
        raise SystemExit("no story yet")
    chunks = chunk_list(project, short=args.short)
    for i, c in enumerate(chunks):
        print(f"{i:03d}|{c}")
    print(f"TOTAL {len(chunks)}")
    return 0


def _qa(args: argparse.Namespace) -> int:
    _path, project = _load(args.slug)
    report = factcheck(project.research)
    project.factcheck = report
    scores = mechanical_qa(project)
    project.qa = scores
    save_project(project, _path)
    print(json.dumps(report.model_dump(), indent=2))
    print(json.dumps(scores.model_dump(), indent=2))
    text = narration_of(project)
    if text:
        print(
            f"words: {word_count(text)} "
            f"(target {CHANNEL.narration_word_min}-{CHANNEL.narration_word_max})"
        )
    weak = scores.critical_below(CHANNEL.qa_revision_threshold)
    if weak:
        print("revise:", ", ".join(weak))
        return 1
    if not report.ok:
        return 1
    return 0


def _compile(args: argparse.Namespace) -> int:
    path, project = _load(args.slug)
    written = compile_project(project, stubs_ok=args.stubs)
    save_project(project, path)
    for k, v in written.items():
        print(f"{k}: {v}")
    spec = spec_path(project.slug)
    print("lint: .venv/bin/python scripts/lint_story.py", spec.relative_to(ROOT))
    print("jobs: GenerateImage using fixtures/*image_jobs.json prompts")
    print("voice+assemble: scripts/run_short.py then scripts/run_custom_video.py")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="channel", description=CHANNEL.name)
    sub = p.add_subparsers(dest="cmd", required=True)

    init = sub.add_parser("init", help="parse title and write a project skeleton")
    init.add_argument("title")
    init.add_argument("--instructions", default="")
    init.add_argument("--duration", type=int, default=None)
    init.add_argument("--skip-seed", action="store_true")
    init.set_defaults(func=_init)

    an = sub.add_parser("analyze", help="parse a title, print JSON, write nothing")
    an.add_argument("title")
    an.add_argument("--instructions", default="")
    an.add_argument("--duration", type=int, default=None)
    an.set_defaults(func=_analyze)

    rs = sub.add_parser("research-seed", help="re-fetch encyclopedia seed")
    rs.add_argument("slug")
    rs.set_defaults(func=_research_seed)

    ch = sub.add_parser("chunks", help="print narration chunks for scene 1:1")
    ch.add_argument("slug")
    ch.add_argument("--short", action="store_true")
    ch.set_defaults(func=_chunks)

    q = sub.add_parser("qa", help="mechanical factcheck + retention flags")
    q.add_argument("slug")
    q.set_defaults(func=_qa)

    c = sub.add_parser("compile", help="write fixtures, stills, spec, image jobs")
    c.add_argument("slug")
    c.add_argument("--stubs", action="store_true", help="pad missing scenes from narration")
    c.set_defaults(func=_compile)

    args = p.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
