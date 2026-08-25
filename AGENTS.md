# AGENTS.md

Working contract for every agent (local or Cloud) with **empty chat history**.
Detailed specs: `docs/video-engine/`. Channel playbooks: `docs/custom-videos.md`, `docs/behind-the-business.md`, `docs/how-they-took-over.md`.

## What this project is

A multi-channel automated animated documentary engine (`channel/`), plus a separate LangGraph `graph/` skeleton that is **not** used for these YouTube titles.

## Current channel modes

| Public name | `--channel` |
|---|---|
| What They Really Think | `what_they_really_think` |
| How They Really Make Money | `behind_the_business` (alias `how_they_really_make_money`) |
| How They Took Over | `how_they_took_over` |

Pass `--channel` explicitly. Do not infer it from the title. Do not mix story or visual grammars.

Sacred for every video: **Fresh research for every video.** **Different story architecture** for each company. **Original narration, not rewritten articles or YouTube transcripts.** **Unique scenes and diagrams** built around that company's actual business. Plus **unique story engine**.

## How to generate a video

Canonical (isolated job, parallel-safe):

```text
.venv/bin/python -m channel generate --channel what_they_really_think --title "What Einstein Really Thought About God"
.venv/bin/python -m channel generate --channel behind_the_business --title "How Visa Really Makes Money"
.venv/bin/python -m channel generate --channel how_they_took_over --title "How Nvidia Took Over AI"
```

Or `.venv/bin/python -m channel generate --job jobs/example.json`.

Then fill `artifacts/<JOB_ID>/project.json` using the prompt module in the manifest. Resume: `python -m channel generate --resume <JOB_ID>`. GenerateImage only after `originality_score` ≥ 80 and `ready_to_publish`. Assemble with `scripts/run_short.py` and `scripts/run_custom_video.py` on the **job** spec. Smoke: `--smoke-test`. Check: `python -m channel cloud-readiness`.

Sequential local init still exists: `python -m channel init` writes `channel/projects/<slug>/`. Cloud Agents should use `generate` so jobs do not collide.

Paste-ready Cloud prompt: `docs/video-engine/CLOUD_AGENT_START_PROMPT.md`.
Quality-bar prompt (kid map, cartoon locks, oversized stills, punchy Shorts): `docs/video-engine/QUALITY_BAR_START_PROMPT.md`.

```text
DO NOT MODIFY THE VIDEO ENGINE, CHANNEL PROMPTS, GLOBAL STYLE, MODEL CONFIGURATION, OR QA THRESHOLDS DURING A NORMAL VIDEO GENERATION TASK.
```

## Where configuration lives

- Channels / voice / style: `channel/config.py` (`CHANNEL`, `BEHIND_THE_BUSINESS`, `HOW_THEY_TOOK_OVER`)
- Versions / model lock / render lock: `channel/engine.py`
- Mode aliases: `channel/modes.py`
- Shipped voice/style locks: `channel/locks.py` (Costco Kokoro **0.92**; new titles **1.0–1.15**, default **1.15**)
- Public-figure cartoon faces: `channel/character_locks.json` + hashed photo/sheet files in `channel/character_sheets/`
- Quality bar (grammar of the best-performing uploads): `docs/video-engine/QUALITY_BAR.md` and `channel/quality_bar.py`

## Where prompts live

`channel/agent_prompts.py` (Think), `channel/business_prompts.py` (Money), `channel/takeover_prompts.py` (Takeover). Index: `prompts/README.md`. Dispatch: `channel/stage_prompts.py`.

## Where artifacts are created

`artifacts/<JOB_ID>/` (manifest, project, fixtures, final, report). Do not commit `.mp4` files. Repo-root `fixtures/` is for **shipped** cuts, not parallel Cloud jobs.

## Validation and tests

```text
.venv/bin/python -m channel qa <job_id-or-slug>
.venv/bin/python -m channel cloud-readiness
.venv/bin/pytest tests/test_channel_handoff.py tests/test_portability.py tests/test_how_they_took_over.py tests/test_behind_the_business.py tests/test_character_locks.py tests/test_quality_bar.py
```

Need `the_thought`, GenerateImage after QA, YouTube `Watch the full video:` + synthetic-media disclosure. Lengths: Think, Money, and Takeover **4400–5500** words (~20–25 minutes). Voice Kokoro `am_liam` (roster may rotate). New titles stay at Kokoro **1.0–1.15** (default **1.15**). Write the whole VO so a five-year-old can follow while an adult still learns. **Do not read long numbers** aloud — round to a sayable figure (`about 158 billion`, not `158,359,009,867`). Exact digits stay in claims.

## What must never change without intent

Visual style strings, QA thresholds, Kokoro-only rule, still-first / no real-person `ideate` on the graph path, 24h assemble cadence, channel mode ids.

## Cursor Cloud specific instructions

Install: Python ≥ 3.13, `pip install -e ".[dev]"`, ffmpeg before assemble. `.cursor/environment.json` is the Cloud bootstrap. Documentary path does **not** need `FAL_KEY` or `ELEVENLABS_API_KEY`; if Kokoro or GenerateImage is missing, **stop** — no fallback. Parallel agents each get a unique job ID under `artifacts/`. Missing secrets: fail clearly. After assemble, print job ID, final/thumb/Short paths, and `report.txt` scores.

## Custom YouTube cuts (detail)

`docs/custom-videos.md` is the Think production system. Cursor Grok fills research / story / bibles / scenes. Compile writes fixture + stills + spec + image jobs + thumbs + draft YouTube copy. After a Think cut ships, update `docs/videos/`. After Money, `docs/business/`. After Takeover, `docs/takeover/`.

Non-negotiable: unique story engine (`lint_story.py`), **originality_score ≥ 80** vs the last 10 on the **same** channel, `ready_to_publish`, answer the title through a story, child-repeatable `the_thought`, real names spoken (kept out of image prompts), no “today is DATE”, third-person spoken English. Think, Money, and Takeover long cuts **~20–25 minutes** (**4400–5500** words at Kokoro **1.0–1.15**). Neutral GenerateImage filenames (never put `costco` in the filename). Fill-frame 16:9, 3840×2160, Shorts 1080×1920, thumbs 1280×720 JPEG, synthetic-media disclosure, 24h between different-title assembles. Named public figures are a **recognizable cartoon of the real person**; reuse `channel/character_locks.json` and the hashed photo plus sheet in `channel/character_sheets/` as GenerateImage references. Match the **grammar** in `docs/video-engine/QUALITY_BAR.md` (kid map, oversized focal object, unique cinema stills, punchy Short) without cloning a reference-cut spine.

Shared contract: chat is not how the next clone learns the rules. After any production change, update `docs/custom-videos.md`, this file, and `.cursor/rules/custom-videos.mdc` in the same commit. `tests/test_channel_handoff.py` guards the three surfaces.

## LangGraph product (`graph/`) — different pipeline

Phase 1 local skeleton. No real named people as video subjects (`ideate` blocks them). Durable code in `graph/`, adapters disposable. Out of scope here: wiring managed APIs until that skeleton is complete. Do not route documentary titles through it.

## Tech stack (both products)

Reasons in `README.md`. Documentary path actually used: `channel/` + Cursor GenerateImage + Kokoro + FFmpeg. Graph path planned: LangGraph, FastAPI, Modal, fal.ai, etc. Best tool for the role. Never silently swap a locked documentary provider.
