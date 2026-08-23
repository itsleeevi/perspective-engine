# AGENTS.md

Working context for AI coding agents (and humans) contributing to this repository. Read this before making changes. The full design rationale is in `README.md`; this file is the operational contract.

## Project

Perspective Engine: a LangGraph-orchestrated pipeline that produces AI-generated narrative "perspective-shift" videos, with human-in-the-loop review checkpoints and structural character-consistency enforcement.

## Current phase

**Phase 1: local-only graph skeleton.** State schema, node logic, and control flow (fan-out, retry, interrupts), running with mocked model calls, an in-memory or SQLite checkpointer, and local-filesystem assets. No external services (no managed database, object storage, serverless compute, or tracing) are wired in this phase. See the development phases in `README.md` for current scope before adding anything.

## Tech stack

Reasons for each choice are in `README.md`. Summary: LangGraph (orchestration), LangSmith (tracing), FastAPI (backend), Modal (compute), Neon/Postgres (state + checkpointer), Cloudflare R2 (assets), fal.ai (video-model router; image-to-video support is a hard requirement for any model wired), Flux / alternate image model (reference stills, chosen empirically by identity stability), ElevenLabs (voice), Claude or GPT-class behind an adapter (script LLM), Remotion (assembly), YouTube Data API v3 (publish), Next.js (review UI).

Principle: best tool for the role. If a better-fit option for a role exists, propose it rather than defaulting to the incumbent. Verify current model identifiers and pricing before wiring any adapter.

## Code rigor tiers

- `graph/` is **durable code**: the architecture's backbone (state schema, node control flow, retry/fan-out/interrupt logic). Cover it with tests that exercise control flow, not just imports. Plan before changing.
- `adapters/` is **disposable code**: provider clients behind a common interface, expected to be swapped as models change. Keep them thin; do not over-engineer.

## Conventions

- `graph/state.py` is the single source of truth for pipeline state. Nodes read and write against it; no ad hoc dictionaries passed between nodes.
- Node signature: takes the current state, returns a partial state update. Keep nodes pure where practical; side effects (API calls) live in `adapters/`, not inlined in node logic.
- Every shot in `shot_list` is tagged `motion` or `static_pan`, defaulting to `static_pan`. The `motion` path (real video generation) is the expensive one and requires explicit justification.
- Character consistency is structural, not prompt-based: `generate_character_refs` produces a human-approved reference sheet and a persistent style descriptor; every `motion` shot is generated from a per-shot still derived from that sheet, never directly from a text prompt; `quality_gate` includes an identity check of each clip against the sheet.
- Tests for `graph/` must cover: retry-cap behavior (repeated failure escalates rather than looping forever), fan-out correctness (one output per shot, order-independent), interrupt pause/resume (state persists across a pause; nothing downstream runs early), and the still-first rule (a `motion` shot without a derived still is rejected before any video-generation call).

## Invariants (enforced in code, not just documented)

- No real, named, identifiable people as video subjects. Validated at `ideate`. A topic implying a real person is fictionalized or made composite, not generated as-is.
- The synthetic-content disclosure flag is always set at publish on the
  LangGraph product path. The What They Really Think YouTube path appends
  an honest synthetic-media disclosure on long and Shorts descriptions
  (see `channel/youtube.py`).
- Every `motion` shot is animated from a derived still anchored to the approved reference sheet. Direct text-to-video for character shots is not permitted.
- The human-review interrupts (script, images, final) are non-bypassable: no code path may auto-approve them, skip them, or run downstream nodes before they resolve.
- Per-shot retries are capped, then escalate to human review. No indefinite retries, no silent drops.
- Publish cadence is rate-limited in code once the publish step exists.

## Custom YouTube cuts (What They Really Think)

These are fixture-driven illustrated documentaries, not the default graph topic flow. **`docs/custom-videos.md` is the production system.** The reusable engine lives in `channel/`: a new video starts with a title string, not a new Python runner.

```text
.venv/bin/python -m channel init "What Einstein Really Thought About Religion"
```

Cursor Grok fills `channel/projects/<slug>/project.json` (research, story, bibles, scenes) using `channel/agent_prompts.py`. Then `python -m channel qa <slug>` (factcheck + originality_score + ready_to_publish) and `python -m channel compile <slug>` writes fixture + stills + spec + image jobs + long/Shorts thumbnail jobs + draft YouTube copy. Images are Cursor Grok GenerateImage **only after** originality_score ≥ 80 and `ready_to_publish`. Voice is Kokoro (default `am_liam`; new titles may rotate `am_michael` / `am_fenrir`). Never Edge, never ElevenLabs. After assemble, `python -m channel youtube <slug>` stamps chapter times and burns the 1280×720 and 1080×1920 JPEGs. Every Short ends on a branded card: watch the full video, link in the description. After a cut ships, update `docs/videos/` so the next agent does not copy the last storyline.

Non-negotiable for that path: unique story per title, **unique story engine** (one object / place / reversal that would not work on any other cut — `lint_story.py` blocks reused chapter cards, a too-close `the_thought`, and the "Month Year. Name…" cold open), **originality_score ≥ 80** vs the last 10 videos and **`ready_to_publish`** before any still (`lint_originality.py` / `python -m channel qa`), **answer the title through a story** (not a Wikipedia biography), one child-repeatable `the_thought` / title payoff in the fixture and in the VO, a blunt simple spine a five-year-old can retell, real org/product names spoken (kept out of image prompts), no "today is DATE" in the VO, third-person spoken English, long cuts **~20–25 minutes** (4400–5500 words), calendar years written as digits (`1995`) while Kokoro speaks the year, character bibles without historical names in image prompts, signature prop obvious every time it returns, global flat-2D style from `channel/config.py` plus a per-title palette accent on new titles, whisper-forced-aligned sync, silent black chapter cards, burned-in scene captions (Shorts in the YouTube safe band), fill-frame 16:9, YouTube thumbs as 1280×720 JPEG. YouTube descriptions (long and Shorts) include an honest synthetic-media disclosure. Shorts description is `Watch the full video:` + `https://youtu.be/<id>` + punch paragraph + disclosure. Different titles wait 24 hours between assembles (`--force` to override). Tick YouTube Studio's altered/synthetic content checkbox on upload.

Shared contract: chat is not how the next clone learns the rules. After any
production change, update `docs/custom-videos.md`, this file, and
`.cursor/rules/custom-videos.mdc` in the same commit (plus lints/tests and
`docs/videos/` when a cut ships), then push. Other environments only see
git. `tests/test_channel_handoff.py` guards the three surfaces.

## Out of scope for the current phase

No real provider APIs, no managed database / object storage / serverless / tracing configuration, no review UI, and no publish or scheduling integration until the local graph skeleton is complete and tested.
