# What They Really Think — production system

This is the reusable engine for the YouTube channel **What They Really Think**. It is written so a Cursor Grok agent can produce a new video from a title, without editing Python. Read this fully before starting. After a cut lands, update `docs/videos/`.

The LangGraph HITL pipeline in `graph/` is a different product (fictional rank-POV videos). Do not route these titles through `ideate` — that node blocks real named people. This path is `channel/` → fixtures → Kokoro → FFmpeg.

## The only required input

```text
TITLE = "What Einstein Really Thought About Religion"
```

Optional:

```text
TARGET_DURATION          # seconds, default 270
SPECIAL_INSTRUCTIONS     # tone, emphasis, things to avoid
```

Everything else is generated: who X and Y are, the relationship, research, story, narration, character/location bibles, scenes, image jobs, voice, and the MP4.

The same pipeline must work when Y is a person, a country, a religion, an ideology, a company, an idea, an event, or a group. Do not hardcode a person into `channel/config.py`. Story content lives in `channel/projects/<slug>/project.json`.

## What these videos are

Entertaining illustrated documentaries. The viewer clicks a mystery title and leaves having heard a **story that answers it**.

They must not feel like Wikipedia read aloud, a school essay, a quote list, a slideshow, or a lecture.

Retention contract: **question → answer → new question**, not fact → fact → fact. Every ~20–30 seconds, something new (a date, a letter, a reversal, a place). Biography is supporting material only — include it when it explains the opinion, otherwise cut it.

`the_thought` in the fixture is the **title payoff**: one sentence a child could repeat that answers the title. Say it, show it, say it again. Narration around it is an intelligent person telling a fascinating story to a friend — not baby talk, not a professor.

## Architecture

| Piece | Role |
|---|---|
| `channel/config.py` | Permanent style, voice, pacing. No people. |
| `channel/schema.py` | Shared `VideoProject` (research, story, bibles, scenes). |
| `channel/title.py` | Agent 1 — parse `What X Really Thought/Thinks About Y`. |
| `channel/research.py` | Encyclopedia **seed** only. Agent adds primary-source claims. |
| `channel/factcheck.py` | Mechanical quote/source checks. |
| `channel/agent_prompts.py` | Stage prompts for Cursor Grok (research → story → scenes). |
| `channel/prompts.py` | Image prompt assembler: global style + bible + action. |
| `channel/compile.py` | Writes fixture, stills module, spec, image jobs. |
| `scripts/lint_story.py` / `lint_storyboard.py` | Novelty, voice, 1:1 chunks, prop/set economy. |
| Cursor **GenerateImage** | Stills. Grok only. Never fal / OpenAI images on this path. |
| Kokoro `am_liam` | Free narration. Never Edge, never ElevenLabs. |
| `scripts/run_custom_video.py` / `run_short.py` | Whisper-aligned assemble. |

```text
TITLE
  → TITLE ANALYZER (code)
  → RESEARCH (agent + seed)
  → FACT CHECK (code + agent)
  → STORY ARCHITECT + NARRATION (agent)
  → CHARACTER / LOCATION BIBLES (agent)
  → RETENTION QA (code + agent)
  → SCENE BREAKDOWN 1:1 with chunks (agent)
  → VISUAL PROMPTS (code)
  → VISUAL QA (code + agent)
  → GenerateImage (Cursor Grok)
  → Kokoro + FFmpeg
  → SHORT + METADATA
```

## Execution checklist (mechanical)

```text
 1. Read this file + docs/videos/README.md + the last video's page
    (do not copy its spine; lint_story will fail you).

 2. .venv/bin/python -m channel init "What X Really Thought About Y"
    Optional: --instructions "..." --duration 270 --skip-seed
    Writes channel/projects/<slug>/project.json

 3. RESEARCHER (Cursor Grok). Fill research.claims with sourced evidence.
    Never invent quotes. Flag contradictions. If evidence is thin, say so.

 4. .venv/bin/python -m channel qa <slug>
    Fix rejected claims. Do not write narration until factcheck is honest.

 5. STORY ARCHITECT + NARRATION WRITER using channel/agent_prompts.py
    650–750 words, 4–6 chapter names, spoken English, title_payoff said
    in the VO. Cold open is the mystery, never "X was born".

 6. BIBLES. Recurring people get ids + visual_lock WITHOUT historical names.
    Locations get ids. Optional signature_prop (≤ 6 scenes).

 7. .venv/bin/python -m channel chunks <slug>
    Write one Scene per line, rotating shot types, visual verbs.

 8. SHORT (one per long video): surprising hook, not a summary.
    Last line: "The full story is on this channel."

 9. .venv/bin/python -m channel qa <slug>
    If a critical score is below 8, rewrite only the weak section.

10. .venv/bin/python -m channel compile <slug>
    Writes fixtures/<slug>.json, *_stills.py, video_specs/<slug>.json,
    and fixtures/<slug>_v1_image_jobs.json
    (--stubs only for scaffolding; never ship stubs)

11. .venv/bin/python scripts/lint_story.py fixtures/video_specs/<slug>.json
    Rewrite until it passes. Then --short if a Short exists.

12. .venv/bin/python scripts/lint_storyboard.py fixtures/video_specs/<slug>.json

13. GenerateImage each job in the jobs JSON (batches of ~16). 16:9 long,
    9:16 Short. Filename = job.filename. On a safety block, retry once
    with historical names already stripped (compile already strips them).

14. .venv/bin/python scripts/run_short.py fixtures/video_specs/<slug>.json
    then
    .venv/bin/python scripts/run_custom_video.py fixtures/video_specs/<slug>.json
    Never two assembles at once.

15. Verify: ffprobe duration + resolution; sync.max_cut_error_ms < 20;
    spot-check frames for letterbox. Thumbnail 1280×720 JPEG.
    Description: search phrase in the first 200 characters, disclosure line.

16. Update docs/videos/<slug>.md + README.md with a "## Do not copy" list
    of quoted phrases. Commit code+docs only when asked. Never commit
    assets/ or .env.
```

Equivalent: `.venv/bin/python scripts/run_title.py "What X Really Thought About Y"` (defaults to `init`).

## Voice (free, in sync)

- **Engine:** Kokoro `am_liam` at speed **1.15**, ~185 wpm, **one utterance per scene** plus a 0.28s hold so the cut lands on a breath. Never Edge, never ElevenLabs.
- **Captions:** each narrated still burns a stylish lower-third of that scene's line. Silent chapter cards stay type-only. Spec field `burn_captions` (default on for channel).
- Shipped older cuts may use different speeds (leave those specs alone).
- **Sync:** faster-whisper word timestamps; `sync.max_cut_error_ms` < 20 after render.
- Chunk windows for new channel videos: 3–7 seconds (target 4.5). Spec fields `chunk_min_seconds` / `chunk_max_seconds` / `chunk_target_seconds` are applied before chunking so they cannot leak from a previous run.

## Pictures

- One Grok still per narration chunk, from `fixtures/<prefix>image_jobs.json`.
- **Global style is frozen** in `channel/config.py` (`GLOBAL_VISUAL_STYLE`). Agents fill action and composition only. Compile prepends the prefix.
- Flat 2D educational animation: simplified faces, flat color, muted historical palette. Not photoreal, not 3D, not anime, not painterly.
- Historical personal names stay **out** of image prompts. Identity is the character bible `visual_lock`.
- Fill the frame. Cover-crop keeps the **top** of 3:2 Grok stills so on-image labels are never sheared. Thumbs are **1280×720 JPEG**.
- Composition changes every ~3–6 seconds. Style does not.

## The Short

One Short per long video. Not a summary. The single most surprising piece, 30–50 seconds, 9:16, open loop to the long video. Lint with `lint_story.py <spec> --short`.

## Hard invariants

- New title = new story. Never clone a shipped beat sheet.
- Third-person narrator. Synthetic-content disclosure always on.
- No Nazi flags/swastikas/camps/gore; no real-person photoreal faces; no cloning a real person's voice.
- Do not invent quotes or private thoughts. If the evidence cannot establish what they thought, say so in the story.
- Do not run two assemble scripts at once (`_ENCODE_CONCURRENCY = 3`).
- Do not hardcode a person into the engine. Only the title changes.
