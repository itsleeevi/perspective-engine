# Provider decisions

Why each dependency was chosen, what it's replacing (if anything), and where the choice will likely be revisited. Model and provider names move quickly: verify current identifiers and pricing before wiring any adapter; the ones below were verified against the dates noted in the adapter source files.

Design principle behind all of these: **best tool for the role**. Each dependency is chosen for fit, with a stated reason. If a better-fit option appears, it should replace the incumbent; none of these are treated as permanent.

## Orchestration: LangGraph (Python)

Durable checkpointing, human-in-the-loop interrupts, and conditional retry/branching are first-class primitives here, not bolted on. Role-based frameworks (CrewAI) and conversation-centric frameworks (AutoGen) prototype faster but don't give the execution control this pipeline depends on; single-vendor agent SDKs would lock model choice, which conflicts with per-shot model routing (cheap model for static pans, best available for motion). Full comparison in [`decisions/0001-core-architecture.md`](decisions/0001-core-architecture.md).

## Script / shot-breakdown / quality-check LLM: Anthropic Claude (currently Haiku 4.5)

Adapter-based (`adapters/llm/`), so swapping to GPT-class or another provider is a new adapter, not an orchestration change. The quality gap for structured script generation and JSON-schema shot breakdowns is small across current frontier/fast models; Haiku 4.5 was chosen for cost given it runs on every shot's quality/identity check, not just once per run.

## Image generation: fal.ai, FLUX.1 [dev]

Used for both the reference sheet (text-to-image) and every per-shot derived still (image-to-image, conditioned on the reference sheet at `strength=0.7` to preserve identity while adapting to the shot). FLUX.1 [dev]'s image-to-image endpoint is what makes the still-first rule practical. An alternate image model is worth an empirical A/B specifically on identity stability across pose/scene changes, since that's the property this pipeline depends on most.

## Video generation: fal.ai, Seedance 2.0 Fast (image-to-video)

fal.ai acts as a model router: one API surface over multiple current video models, so per-shot model selection is a parameter rather than a separate integration per vendor. Seedance 2.0 Fast was selected because it supports image-to-video with lower latency than the standard tier, and image-to-video support is a hard requirement for any model wired here. Text-to-video is never used for character shots (see [Character consistency](../README.md#character-consistency)).

## Voice: ElevenLabs (eleven_multilingual_v2)

Narration quality and multilingual support, with a configurable voice ID (`ELEVENLABS_VOICE_ID`) so the default narrator voice is a config change, not a code change.

## Assembly: FFmpeg today, Remotion planned

The current `assemble` node does real work: downloads every fal.ai-hosted asset, converts static-pan stills into fixed-duration video segments, concatenates all shots in shot order, and mixes in the ElevenLabs voiceover, all via subprocess `ffmpeg` calls. This is not a stub or placeholder.

Remotion is the planned replacement once captions, transitions, and motion graphics are needed; programmatic composition suits that better than shelling out to FFmpeg for every effect. The output contract (`final_video_path`, a local `file://` MP4 path) is designed to stay the same across that migration.

## Planned, not yet wired

These appear in the [Roadmap](../README.md#roadmap) because the local-prototype phase intentionally defers paid/managed infrastructure until the core control flow is proven (see [`docs/roadmap.md`](roadmap.md)):

- **Observability: LangSmith.** Model- and framework-agnostic tracing of every node call, retry, and interrupt. A multi-node graph with parallel branches is impractical to debug blind once real providers are live continuously.
- **Backend: FastAPI.** Already used for the review UI (`webui/`); will grow into the full API service once a persistent backend is needed.
- **Compute: Modal.** Serverless functions per stage, suited to bursty parallel shot generation.
- **State / persistence: Neon (serverless Postgres).** Replaces the local SQLite/in-memory checkpointer with a durable one so a run backed by a real graph process can pause at a review gate and resume from anywhere.
- **Object storage: Cloudflare R2.** S3-compatible, no egress fees. State already stores asset URLs rather than binaries, so this is a storage-backend swap, not a schema change.
- **Review UI: Next.js.** A fuller dashboard than the current lightweight FastAPI + static-HTML review UI, once more than "approve/reject/edit-one-field" is needed.
- **Publishing: YouTube Data API v3.** Rate-limited in code once wired; `publish` already enforces the cadence cap against mock output today.
