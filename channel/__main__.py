"""CLI: title in → project files out.

    .venv/bin/python -m channel init "What Einstein Really Thought About Religion"
    .venv/bin/python -m channel init --channel behind_the_business "How Costco Really Makes Money"
    .venv/bin/python -m channel init --channel how_they_took_over "How Nvidia Took Over AI"

Subcommands:
    init           parse title, seed research, write project skeleton
    analyze        parse a title and print JSON (no files)
    research-seed  re-fetch the encyclopedia seed into an existing project
    chunks         print narration chunks (needs a story)
    compile        write fixtures / stills / spec / image jobs / youtube pack
    qa             factcheck + retention + originality + monetization
    score-title    score a title for the selected channel
    suggest-titles score title patterns for a company / subject
    originality    compare this title to the last 10 shipped videos
    youtube        write description, tags, 1280×720 + 9:16 Shorts thumbs
    branding       size a profile (800×800) and cover (2560×1440) for YouTube
    generate       isolated job under artifacts/<job_id>/ (canonical Cloud command)
    cloud-readiness check configs, prompts, rules, writable artifacts
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from channel.compile import chunk_list, compile_project
from channel.config import config_for
from channel.io import load_project, save_project
from channel.modes import CHANNEL_FLAG_HELP, ChannelMode, parse_mode
from channel.paths import ROOT, project_dir, spec_path
from channel.qa import narration_of, run_full_qa, word_count
from channel.research import seed_research
from channel.schema import BusinessContext, ResearchPack, TakeoverContext, VideoProject
from channel.slug import slugify
from channel.title import analyze_title


def _init(args: argparse.Namespace) -> int:
    mode = parse_mode(args.channel)
    analysis = analyze_title(
        args.title,
        special_instructions=args.instructions or "",
        target_duration_seconds=args.duration,
        channel_mode=mode,
    )
    slug = slugify(analysis.title)
    d = project_dir(slug)
    d.mkdir(parents=True, exist_ok=True)
    pack = ResearchPack(subject=analysis.subject, target=analysis.target)
    if not args.skip_seed:
        pack = seed_research(analysis)
    business = None
    takeover = None
    if mode is ChannelMode.behind_the_business:
        business = BusinessContext(
            company=analysis.company or analysis.subject,
            industry=analysis.industry,
            business_question=analysis.business_question or analysis.core_question,
            apparent_business=analysis.apparent_business,
            potential_hidden_engine=analysis.potential_hidden_engine,
            customer=analysis.customer,
            likely_revenue_streams=list(analysis.likely_revenue_streams),
        )
    elif mode is ChannelMode.how_they_took_over:
        takeover = TakeoverContext(
            subject=analysis.subject,
            arena=analysis.arena,
            starting_position=analysis.starting_position,
            current_position=analysis.dominant_position,
        )
    project = VideoProject(
        title=analysis.title,
        slug=slug,
        channel_mode=mode,
        analysis=analysis,
        business=business,
        takeover=takeover,
        research=pack,
        special_instructions=analysis.special_instructions,
    )
    save_project(project, d / "project.json")
    (d / "README.md").write_text(
        _agent_readme(slug, analysis.title, mode),
        encoding="utf-8",
    )
    print(f"project: {d / 'project.json'}")
    print(f"channel_mode={mode.value}")
    if mode is ChannelMode.behind_the_business:
        print(f"company={analysis.company!r} question={analysis.business_question}")
    elif mode is ChannelMode.how_they_took_over:
        print(
            f"subject={analysis.subject!r} arena={analysis.arena!r} "
            f"question={analysis.core_question}"
        )
    else:
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
        channel_mode=parse_mode(args.channel),
    )
    print(analysis.model_dump_json(indent=2))
    return 0


def _score_title(args: argparse.Namespace) -> int:
    mode = parse_mode(args.channel)
    analysis = analyze_title(args.title, channel_mode=mode)
    if mode is ChannelMode.how_they_took_over:
        from channel.takeover_titles import score_takeover_title

        print(json.dumps(score_takeover_title(args.title, analysis=analysis), indent=2))
        return 0
    from channel.business_titles import score_business_title

    print(json.dumps(score_business_title(args.title, analysis=analysis), indent=2))
    return 0


def _suggest_titles(args: argparse.Namespace) -> int:
    mode = parse_mode(args.channel)
    if mode is ChannelMode.how_they_took_over:
        from channel.takeover_titles import suggest_takeover_titles

        print(json.dumps(suggest_takeover_titles(args.company, y=args.y or ""), indent=2))
        return 0
    from channel.business_titles import suggest_business_titles

    print(json.dumps(suggest_business_titles(args.company, y=args.y or ""), indent=2))
    return 0


def _research_seed(args: argparse.Namespace) -> int:
    path, project = _load(args.slug)
    project.research = seed_research(project.analysis)
    save_project(project, path)
    print(f"seed sources: {len(project.research.seed_sources)}")
    return 0


def _agent_readme(slug: str, title: str, mode: ChannelMode | None = None) -> str:
    from channel.stage_prompts import stage_prompts_for

    prompts = stage_prompts_for(mode)
    cfg = config_for(mode)
    docs = {
        ChannelMode.behind_the_business: f"docs/business/{slug}.md",
        ChannelMode.how_they_took_over: f"docs/takeover/{slug}.md",
    }.get(mode, f"docs/videos/{slug}.md")
    return f"""# {title}

Working directory for this video. Story content lives in `project.json`.
Channel mode: `{cfg.mode.value}` (`{cfg.name}`).
Style, voice, and QA rules live in `channel/config.py` — do not copy a person or company into that file.

## Pipeline

1. Researcher — {prompts.RESEARCHER.strip().splitlines()[0]}
2. Fact check + originality + monetization — `python -m channel qa {slug}`
3. Story architect, bibles, narration ({cfg.narration_word_min}–{cfg.narration_word_max} words)
4. `python -m channel chunks {slug}`
5. Scene breakdown, 1:1 with chunks
6. `python -m channel compile {slug}` then `scripts/lint_originality.py`
7. GenerateImage each job in `fixtures/{slug}_v1_image_jobs.json` (Cursor Grok)
8. GenerateImage `fixtures/{slug}_thumbnail_image_jobs.json` and
   `fixtures/{slug}_short_thumbnail_image_jobs.json`, then `python -m channel youtube {slug}`
9. `.venv/bin/python scripts/run_short.py fixtures/video_specs/{slug}.json`
10. `.venv/bin/python scripts/run_custom_video.py fixtures/video_specs/{slug}.json`
11. Update `{docs}`

Voice is Kokoro (default `{cfg.kokoro_voice}`; new titles may rotate). Never Edge. Never ElevenLabs.
Images are Cursor Grok GenerateImage. Do not invent quotes or numbers.
"""


def _load(slug: str) -> tuple[Path, VideoProject]:
    from channel.job import resolve_project_path

    try:
        path = resolve_project_path(slug)
    except FileNotFoundError as exc:
        raise SystemExit(
            f"{exc} — run: python -m channel generate --channel <mode> --title \"…\""
        ) from exc
    return path, load_project(path)


def _job_root(project_file: Path) -> Path | None:
    from channel.job import artifact_job_root

    return artifact_job_root(project_file)


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
    from channel.job import persist_project_sidecars

    persist_project_sidecars(project, _path.parent)
    print(json.dumps(report.model_dump(), indent=2))
    print(json.dumps(scores.model_dump(), indent=2))
    if originality:
        print(json.dumps(originality.model_dump(exclude={"comparisons"}), indent=2))
    if monetization:
        print(json.dumps(monetization.model_dump(), indent=2))
    if project.business_qa:
        print(json.dumps(project.business_qa.model_dump(), indent=2))
    if project.takeover_qa:
        print(json.dumps(project.takeover_qa.model_dump(), indent=2))
    text = narration_of(project)
    cfg = config_for(project.channel_mode)
    if text:
        print(
            f"words: {word_count(text)} "
            f"(target {cfg.narration_word_min}-{cfg.narration_word_max})"
        )
    weak = scores.critical_below(cfg.qa_revision_threshold)
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
    from channel.engine import image_token_for

    path, project = _load(args.slug)
    job_root = _job_root(path)
    written = compile_project(
        project,
        stubs_ok=args.stubs,
        root=job_root,
        image_token=image_token_for(
            project.slug, path.parent.name if job_root else None
        ),
    )
    from channel.originality import originality_report_for_slug, regenerate_targets
    from channel.monetization_qa import compute_monetization_readiness

    if not args.stubs and not args.force:
        originality = originality_report_for_slug(project.slug)
        project.originality = originality
        project.monetization = compute_monetization_readiness(project, originality)
    save_project(project, path)
    from channel.job import persist_project_sidecars

    persist_project_sidecars(project, path.parent)
    for k, v in written.items():
        print(f"{k}: {v}")
    spec = spec_path(project.slug, _job_root(path))
    try:
        spec_rel = spec.relative_to(ROOT)
    except ValueError:
        spec_rel = spec
    print("lint: .venv/bin/python scripts/lint_story.py", spec_rel)
    print("originality: .venv/bin/python scripts/lint_originality.py", spec_rel)
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
        write_channel_copy,
    )

    mode = args.channel or None
    if not args.profile and not args.cover:
        raise SystemExit("pass --profile and/or --cover")
    if args.profile:
        src = Path(args.profile)
        if not src.is_file():
            raise SystemExit(f"no profile still at {src}")
        out = render_profile_jpeg(src, mode=mode)
        print(f"profile {PROFILE_W}x{PROFILE_H}: {out}")
    if args.cover:
        src = Path(args.cover)
        if not src.is_file():
            raise SystemExit(f"no cover still at {src}")
        banner = render_banner_jpeg(src, mode=mode)
        preview = write_banner_safezone_preview(banner, mode=mode)
        print(f"cover {BANNER_W}x{BANNER_H}: {banner}")
        print(f"safe-zone preview (do not upload): {preview}")
    copy = write_channel_copy(mode=mode)
    print(f"about: {copy['about']}")
    if copy["handle"].is_file():
        print(f"handle: {copy['handle']}")
    return 0


def _generate(args: argparse.Namespace) -> int:
    from channel.generate import run_generate

    return run_generate(args)


def _cloud_readiness(args: argparse.Namespace) -> int:
    from channel.readiness import check_readiness, print_readiness

    return print_readiness(check_readiness(strict=bool(args.strict)))


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="channel",
        description=(
            "Shared video engine (What They Really Think / "
            "How They Really Make Money / How They Took Over)"
        ),
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    init = sub.add_parser("init", help="parse title and write a project skeleton")
    init.add_argument("title")
    init.add_argument(
        "--channel",
        default="what_they_really_think",
        help=CHANNEL_FLAG_HELP,
    )
    init.add_argument("--instructions", default="")
    init.add_argument("--duration", type=int, default=None)
    init.add_argument("--skip-seed", action="store_true")
    init.set_defaults(func=_init)

    an = sub.add_parser("analyze", help="parse a title, print JSON, write nothing")
    an.add_argument("title")
    an.add_argument(
        "--channel",
        default="what_they_really_think",
        help=CHANNEL_FLAG_HELP,
    )
    an.add_argument("--instructions", default="")
    an.add_argument("--duration", type=int, default=None)
    an.set_defaults(func=_analyze)

    st = sub.add_parser(
        "score-title",
        help="score a title (1–10 dimensions + TITLE_SCORE)",
    )
    st.add_argument("title")
    st.add_argument(
        "--channel",
        default="behind_the_business",
        help=CHANNEL_FLAG_HELP,
    )
    st.set_defaults(func=_score_title)

    sg = sub.add_parser(
        "suggest-titles",
        help="fill title patterns for a company/subject and score them",
    )
    sg.add_argument("company")
    sg.add_argument("--y", default="", help="optional second noun (arena / From Y)")
    sg.add_argument(
        "--channel",
        default="behind_the_business",
        help=CHANNEL_FLAG_HELP,
    )
    sg.set_defaults(func=_suggest_titles)

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
    br.add_argument(
        "--channel",
        default="",
        help=CHANNEL_FLAG_HELP,
    )
    br.set_defaults(func=_branding)

    gen = sub.add_parser(
        "generate",
        help="create or resume an isolated artifacts/<job_id> generation job",
    )
    gen.add_argument("--channel", default="", help=CHANNEL_FLAG_HELP)
    gen.add_argument("--title", default="")
    gen.add_argument("--job", default="", help="JSON job file with channel + title")
    gen.add_argument("--resume", default="", help="existing job_id")
    gen.add_argument("--job-id", dest="job_id", default="")
    gen.add_argument("--instructions", default="")
    gen.add_argument("--duration", type=int, default=None)
    gen.add_argument("--duration-minutes", dest="duration_minutes", type=float, default=None)
    gen.add_argument("--skip-seed", action="store_true")
    gen.add_argument("--smoke-test", action="store_true")
    gen.add_argument("--stubs", action="store_true")
    gen.add_argument("--force", action="store_true")
    gen.add_argument("--artifacts", default="", help="override artifacts root (tests)")
    gen.set_defaults(func=_generate)

    ready = sub.add_parser("cloud-readiness", help="verify a fresh clone can generate")
    ready.add_argument("--strict", action="store_true", help="fail if ffmpeg is missing")
    ready.set_defaults(func=_cloud_readiness)

    args = p.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
