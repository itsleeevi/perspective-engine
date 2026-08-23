"""CLI: title in → project files out.

    .venv/bin/python -m channel init "What Einstein Really Thought About Religion"

Subcommands:
    init           parse title, seed research, write project skeleton
    analyze        parse a title and print JSON (no files)
    research-seed  re-fetch the encyclopedia seed into an existing project
    chunks         print narration chunks (needs a story)
    compile        write fixtures / stills / spec / image jobs / youtube pack
    qa             factcheck + retention + originality + monetization
    originality    compare this title to the last 10 shipped videos
    youtube        write description, tags, 1280×720 + 9:16 Shorts thumbs
    branding       size a profile (800×800) and cover (2560×1440) for YouTube
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from channel.compile import chunk_list, compile_project
from channel.config import CHANNEL
from channel.io import load_project, save_project
from channel.paths import ROOT, project_dir, spec_path
from channel.qa import narration_of, run_full_qa, word_count
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
2. Fact check + originality + monetization — `python -m channel qa {slug}`
3. Story architect, bibles, narration (4400–5500 words, ~20–25 minutes)
4. `python -m channel chunks {slug}`
5. Scene breakdown, 1:1 with chunks
6. `python -m channel compile {slug}` then `scripts/lint_originality.py`
7. GenerateImage each job in `fixtures/{slug}_v1_image_jobs.json` (Cursor Grok)
8. GenerateImage `fixtures/{slug}_thumbnail_image_jobs.json` and
   `fixtures/{slug}_short_thumbnail_image_jobs.json`, then `python -m channel youtube {slug}`
9. `.venv/bin/python scripts/run_short.py fixtures/video_specs/{slug}.json`
10. `.venv/bin/python scripts/run_custom_video.py fixtures/video_specs/{slug}.json`
11. Update `docs/videos/{slug}.md`

Voice is Kokoro (default `{CHANNEL.kokoro_voice}`; new titles may rotate). Never Edge. Never ElevenLabs.
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
    report, scores, originality, monetization = run_full_qa(project)
    save_project(project, _path)
    print(json.dumps(report.model_dump(), indent=2))
    print(json.dumps(scores.model_dump(), indent=2))
    if originality:
        print(json.dumps(originality.model_dump(exclude={"comparisons"}), indent=2))
    if monetization:
        print(json.dumps(monetization.model_dump(), indent=2))
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
    if originality and not originality.ready_for_images:
        from channel.originality import regenerate_targets

        print("regenerate:", ", ".join(regenerate_targets(originality)))
        return 1
    if monetization and not monetization.ready_to_publish:
        print("monetization: not ready_to_publish —", "; ".join(monetization.notes[:5]))
        return 1
    return 0


def _originality(args: argparse.Namespace) -> int:
    from channel.originality import originality_report_for_slug, regenerate_targets
    from channel.originality_policy import ORIGINALITY_SCORE_MIN

    report = originality_report_for_slug(args.slug)
    print(json.dumps(report.model_dump(exclude={"comparisons"}), indent=2))
    print(f"originality_score: {report.originality_score} (min {ORIGINALITY_SCORE_MIN})")
    if report.comparisons:
        worst = max(report.comparisons, key=lambda c: c.weighted())
        print(f"closest_recent: {worst.compared_slug} weighted={worst.weighted():.0f}")
    if not report.ready_for_images:
        targets = regenerate_targets(report)
        if targets:
            print("regenerate:", ", ".join(targets))
    return 0 if report.ready_for_images else 1


def _compile(args: argparse.Namespace) -> int:
    path, project = _load(args.slug)
    written = compile_project(project, stubs_ok=args.stubs)
    from channel.originality import originality_report_for_slug, regenerate_targets
    from channel.monetization_qa import compute_monetization_readiness

    if not args.stubs and not args.force:
        originality = originality_report_for_slug(project.slug)
        project.originality = originality
        project.monetization = compute_monetization_readiness(project, originality)
    save_project(project, path)
    for k, v in written.items():
        print(f"{k}: {v}")
    spec = spec_path(project.slug)
    print("lint: .venv/bin/python scripts/lint_story.py", spec.relative_to(ROOT))
    print("originality: .venv/bin/python scripts/lint_originality.py", spec.relative_to(ROOT))
    print("jobs: GenerateImage using fixtures/*image_jobs.json prompts")
    print("thumb: GenerateImage the *_thumbnail_image_jobs.json still and")
    print("       the *_short_thumbnail_image_jobs.json still, then")
    print(f"       .venv/bin/python -m channel youtube {project.slug}")
    print("voice+assemble: scripts/run_short.py then scripts/run_custom_video.py")
    if (
        not args.stubs
        and not args.force
        and project.originality
        and not project.originality.ready_for_images
    ):
        print(
            "originality FAILED — do not GenerateImage. Rewrite:",
            ", ".join(regenerate_targets(project.originality)),
            file=sys.stderr,
        )
        return 1
    if (
        not args.stubs
        and not args.force
        and project.monetization
        and not project.monetization.ready_to_publish
    ):
        print(
            "monetization not ready_to_publish — fix QA notes before images:",
            "; ".join(project.monetization.notes[:5]),
            file=sys.stderr,
        )
        return 1
    return 0


def _youtube(args: argparse.Namespace) -> int:
    from channel.shorts import find_short_thumbnail_still
    from channel.thumbnail import render_short_thumbnail_jpeg, render_thumbnail_jpeg
    from channel.youtube import (
        find_thumbnail_still,
        write_pack_for_slug,
        youtube_dir,
        youtube_stem,
    )

    pack = write_pack_for_slug(args.slug)
    for k, v in pack.items():
        print(f"{k}: {v}")
    spec = json.loads(spec_path(args.slug).read_text(encoding="utf-8"))
    text = str((spec.get("youtube") or {}).get("thumbnail_text") or "")
    still = Path(args.still) if args.still else find_thumbnail_still(args.slug)
    if still and still.is_file():
        dest = youtube_dir() / f"{youtube_stem(args.slug)}_thumbnail_1280x720.jpg"
        print(f"thumbnail: {render_thumbnail_jpeg(still, dest, text)}")
    else:
        print("thumbnail: no still yet — GenerateImage the thumbnail job, then rerun with --still")
    short_still = find_short_thumbnail_still(args.slug)
    if short_still and short_still.is_file():
        dest = youtube_dir() / f"{youtube_stem(args.slug)}_short_thumbnail_1080x1920.jpg"
        print(f"shorts thumbnail: {render_short_thumbnail_jpeg(short_still, dest, text)}")
    else:
        print("shorts thumbnail: no still yet — GenerateImage the short thumbnail job")
    return 0


def _branding(args: argparse.Namespace) -> int:
    from channel.branding import (
        BANNER_H,
        BANNER_W,
        PROFILE_H,
        PROFILE_W,
        render_banner_jpeg,
        render_profile_jpeg,
        write_banner_safezone_preview,
    )

    if args.profile:
        src = Path(args.profile)
        if not src.is_file():
            raise SystemExit(f"no profile still at {src}")
        out = render_profile_jpeg(src)
        print(f"profile {PROFILE_W}x{PROFILE_H}: {out}")
    if args.cover:
        src = Path(args.cover)
        if not src.is_file():
            raise SystemExit(f"no cover still at {src}")
        banner = render_banner_jpeg(src)
        preview = write_banner_safezone_preview(banner)
        print(f"cover {BANNER_W}x{BANNER_H}: {banner}")
        print(f"safe-zone preview (do not upload): {preview}")
    if not args.profile and not args.cover:
        raise SystemExit("pass --profile and/or --cover")
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

    q = sub.add_parser(
        "qa",
        help="factcheck + retention + originality + monetization readiness",
    )
    q.add_argument("slug")
    q.set_defaults(func=_qa)

    orig = sub.add_parser(
        "originality",
        help="compare this title to the last 10 shipped videos",
    )
    orig.add_argument("slug")
    orig.set_defaults(func=_originality)

    c = sub.add_parser("compile", help="write fixtures, stills, spec, image jobs, youtube pack")
    c.add_argument("slug")
    c.add_argument("--stubs", action="store_true", help="pad missing scenes from narration")
    c.add_argument(
        "--force",
        action="store_true",
        help="write fixtures even if originality / monetization QA fails",
    )
    c.set_defaults(func=_compile)

    yt = sub.add_parser(
        "youtube",
        help="write description/tags and overlay long + Shorts thumbnail type",
    )
    yt.add_argument("slug")
    yt.add_argument(
        "--still",
        default="",
        help="PNG to cover-crop into assets/youtube/<slug>_thumbnail_1280x720.jpg",
    )
    yt.set_defaults(func=_youtube)

    br = sub.add_parser(
        "branding",
        help="size channel profile 800×800 and cover 2560×1440",
    )
    br.add_argument("--profile", default="", help="square still for the circular icon")
    br.add_argument("--cover", default="", help="16:9 still for the channel banner")
    br.set_defaults(func=_branding)

    args = p.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
