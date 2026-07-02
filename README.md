# Perspective Engine

An agentic pipeline that produces short narrative "perspective-shift" videos using AI video generation, orchestrated as a stateful graph with human review checkpoints built into the architecture.

The videos take a single viewpoint that is hard to film conventionally (for example "a day in the life of a bee," "a photon's journey from the sun to your eye," "the same morning across two very different lives") and render it as a short narrated piece. The system targets two formats: short-form vertical clips (30-60s) and long-form pieces (8-12 min).

This repository is the orchestration system, not the rendered media. It is designed as a system rather than a script for two reasons: the work is genuinely graph-shaped (parallel generation, conditional retries, human-in-the-loop gates), and treating it that way keeps each part independently testable and swappable.

## Design principles

- **Best tool for the role.** Each dependency is chosen for fit, with a stated reason. If a better-fit option appears, it should replace the incumbent.
- **Human review is part of the architecture, not an add-on.** Two approval gates pause execution before and after generation. They cannot be bypassed in code.
- **Identity is generated once and referenced everywhere.** Character consistency across independently generated clips is the hardest problem in AI video storytelling. The pipeline solves it structurally (see Character consistency below), not by hoping per-shot prompts converge.
- **Cost is a first-class concern.** Most shots default to a cheap rendering path; the expensive path is opt-in per shot and logged.
- **Provider independence.** Video and language models sit behind adapters so any one of them can be replaced without touching orchestration logic.

## Tech stack and rationale

The deciding requirements for orchestration are durable checkpointing, human-in-the-loop approval gates, and conditional branching with retries. The stack is chosen against those requirements.

- **Orchestration: LangGraph (Python).** Selected because durable checkpointing, HITL interrupts, and conditional retry/branching are first-class primitives rather than add-ons. Role-based frameworks prototype faster but trade away the execution control and observability this pipeline depends on; single-vendor agent SDKs would lock model choice, which conflicts with per-shot model routing.
- **Observability: LangSmith.** Model- and framework-agnostic tracing of every node call, retry, and interrupt. A multi-node graph with parallel branches is impractical to debug blind.
- **Backend: FastAPI.** Async-native, integrates cleanly with the graph.
- **Compute: Modal.** Serverless functions per stage, suited to bursty parallel generation.
- **State / persistence: Neon (serverless Postgres).** Application state and the LangGraph checkpointer.
- **Object storage: Cloudflare R2.** S3-compatible, no egress fees, for generated media. State stores asset URLs, not binaries.
- **Video generation: fal.ai (model router).** A single API surface over multiple current video models, so per-shot model selection is a parameter rather than a separate integration per vendor. Image-to-video capability is a hard requirement for any model wired here (see Character consistency).
- **Reference images: Flux, with an A/B against an alternate image model for the character-consistency step,** where identity stability across edits matters most. This choice is empirical: the model that best holds a locked identity across pose and scene changes wins the role.
- **Voice: ElevenLabs.** Narration quality and multilingual support.
- **Script / shot-breakdown LLM: provider-agnostic via an adapter** (Claude or GPT-class). The quality gap for structured script generation is small; the adapter keeps it swappable.
- **Quality gate: a vision-capable LLM call** checking both technical quality and character identity against the reference sheet, rather than a bespoke CV model.
- **Assembly: Remotion.** Programmatic video composition (clips, voiceover, captions, pans over stills).
- **Publishing: YouTube Data API v3.**
- **Review UI: Next.js** (minimal approval surface for the two gates).
- **CI: GitHub Actions.**

Model and provider names move quickly. Verify current model identifiers and pricing before wiring any adapter.

## Character consistency

A story is only composite if the character is recognizably the same across every shot. Nothing in current video models guarantees this from text prompts alone, so the pipeline enforces it in four layers:

1. **Character reference sheet.** Before any video generation, `generate_character_refs` produces a model sheet: the character from multiple angles, expressions, and lighting conditions, generated as a consistent set (the same technique traditional animation uses to keep characters on-model). The sheet is human-approved and stored in state as the identity anchor for the entire run.
2. **Image-to-video, never text-to-video.** Shots are not generated from text descriptions of the character. For each shot, a per-shot still of the locked character in the required pose/setting is first derived from the reference sheet (via the image model's reference/edit capability), then the clip is animated from that still. The pattern is `locked identity -> per-shot still -> clip`, with a still as the consistency bridge at every step. The video model animates motion; it never reinvents the character.
3. **Identity check in the quality gate.** `quality_gate` compares each generated clip against the reference sheet using a vision-capable LLM: same character, or drift? Off-model shots fail the gate and route through the capped retry path, then escalate to human review. Consistency becomes a measured, logged property of each run, not an eyeball judgment at the end.
4. **Persistent style descriptor.** `character_refs` carries a fixed text descriptor alongside the images, including one deliberately distinctive identifying detail, appended to every shot prompt. Images anchor identity; the descriptor stops prompts drifting, and the distinctive detail gives both the model and the identity check a concrete feature to hold.

Residual drift is expected with current models; the design goal is that it is caught automatically, retried, and escalated before assembly rather than discovered in the final export.

## Architecture

State is a single typed object (Pydantic) threaded through the graph:

- `topic`, `brief`
- `script`: scene beats, with the opening beat tagged as the hook
- `shot_list`: per shot, an id, prompt, duration, `mode` (`motion` = real video generation, `static_pan` = animated still, the primary cost lever), assigned model, status, retry count, asset URL
- `character_refs`: reference sheet image URLs, per-shot derived stills, and the persistent style descriptor
- `voiceover_url`, `music_url`, `final_video_path`
- `metadata`: title, description, tags, thumbnail, and a synthetic-content disclosure flag (always set)
- `cost_log`: running spend per node
- `human_edits_log`: changes made at each review gate (quality control and audit trail)

Nodes, in order:

1. `ideate`: select or propose a topic. Validates that the subject is not a real, named, identifiable person.
2. `write_script`: generates the script, hook line first.
3. `shot_breakdown`: turns the script into the shot list, tags each shot's render mode, assigns a model.
4. `human_review_script`: **interrupt.** Pauses for approval/edit before any paid generation. Not auto-approvable.
5. `generate_character_refs`: generates the character reference sheet and style descriptor; the identity anchor for the run.
6. `generate_shots`: fan-out. For each shot: derive a per-shot still from the reference sheet, then animate the clip from that still with the shot's assigned model.
7. `quality_gate`: per-shot check covering technical quality and identity match against the reference sheet. Pass continues; fail retries (capped); repeated failure escalates to human. No infinite loops.
8. fan-in once all shots clear.
9. `generate_voiceover`: TTS aligned to shot timings.
10. `assemble`: composes clips, stills, audio, and captions into the final cut.
11. `generate_metadata`: title, description, tags, thumbnail; sets the disclosure flag.
12. `human_review_final`: **interrupt.** Final approval before publish.
13. `publish`: uploads, respecting a hard-coded cadence cap.

Persistence uses the LangGraph checkpointer backed by Postgres, so a run can pause at a review gate and resume later without re-running already-completed steps.

## Invariants

These are enforced in code, not just documented:

- No real, named, identifiable people as video subjects, validated at `ideate`.
- The synthetic-content disclosure flag is always set at publish.
- Every shot is tagged `motion` or `static_pan`, defaulting to `static_pan`.
- Every `motion` shot is generated from a derived still, never directly from text.
- Per-shot retries are capped, then escalate to human review.
- Publish cadence is rate-limited in code.
- Both human-review interrupts are non-bypassable by any code path.

## Repository layout

```
perspective-engine/
├── graph/              # LangGraph: state schema, nodes, edges
│   ├── state.py
│   ├── nodes/
│   └── graph.py
├── adapters/           # provider clients (video, image, voice, llm) behind common interfaces
│   ├── video_gen/
│   ├── image_gen/
│   ├── voice/
│   └── llm/
├── assembly/           # Remotion composition project
├── api/                # FastAPI service
├── dashboard/          # Next.js review UI
├── tests/
├── .github/workflows/
├── .env.example
├── AGENTS.md
└── README.md           # this file
```

## Development phases

The build is sequenced to defer paid infrastructure until the core loop is proven.

- **Phase 1, local only.** Full state schema, node logic, and control flow (fan-out, retry, interrupts), run locally with an in-memory/SQLite checkpointer, local-filesystem assets, and mocked model calls. The goal is correct control flow, covered by tests. No external services.
- **Phase 2, one real video, still local.** Real but inexpensive providers behind the adapters; the full graph triggered from the CLI to produce a single end-to-end video, with the two gates approved from the terminal. Includes the empirical image-model A/B for the character-consistency role.
- **Phase 3, durable infrastructure.** Migrate the checkpointer to Postgres and assets to object storage, add the review UI, move compute to serverless functions, and enable tracing.
- **Phase 4, scheduling.** Automated triggers for the steps suitable for automation, within the cadence cap.

## Working with AI coding agents

This README is the spec; `AGENTS.md` holds the working constraints loaded each session. `graph/` is durable code and is tested and reviewed carefully; `adapters/` is intentionally swappable. Plan before implementing changes to orchestration logic.
