# Provider decisions

Why each dependency was chosen, what it's replacing (if anything), and where the choice will likely be revisited. Model and provider names move quickly: verify current identifiers and pricing before wiring any adapter; the ones below were verified against the dates noted in the adapter source files.

Design principle behind all of these: **best tool for the role**. Each dependency is chosen for fit, with a stated reason. If a better-fit option appears, it should replace the incumbent; none of these are treated as permanent.

## Orchestration: LangGraph (Python)

Durable checkpointing, human-in-the-loop interrupts, and conditional retry/branching are first-class primitives here, not bolted on. Role-based frameworks (CrewAI) and conversation-centric frameworks (AutoGen) prototype faster but don't give the execution control this pipeline depends on; single-vendor agent SDKs would lock model choice, which conflicts with per-shot model routing (cheap model for static pans, best available for motion). Full comparison in [`decisions/0001-core-architecture.md`](decisions/0001-core-architecture.md).

## Script / shot-breakdown LLM: OpenAI, with Anthropic Claude Haiku for the per-shot quality check

Adapter-based (`adapters/llm/`), so swapping providers is a new adapter, not an orchestration change. `OpenAILLMAdapter` handles the two authoring calls (script writing, storyboard visualization); the prompt content behind both is shared verbatim with the Anthropic adapter (`adapters/llm/_prompts.py`), so behavioral fixes for this format live in the prompt, not in provider-specific code. The vision-based quality check still delegates to `AnthropicLLMAdapter` — Claude Haiku is the cheap, adequate choice for a call that runs once per shot (tens of times per video), not once per run.

## Image generation: OpenAI `gpt-image-*` (default), fal.ai FLUX (alternate), Pollinations (free)

`OpenAIImageGenAdapter` is the default for both the reference sheet and per-shot derived stills: it was the only option measured to render in-scene text (title cards, on-screen labels) reliably. Quality defaults to `low` (~$0.0055/image) — `medium` (7.6x the cost) mostly bought storyboard-prompt fixes, not rendering fidelity, and `high` is not recommended at any budget because it drifts off the locked character design. `FalImageGenAdapter` (FLUX.1 [dev]/[schnell], image-to-image conditioned on the reference sheet) remains available via `--image-provider fal` and cannot reliably render text but is cheaper. `PollinationsImageGenAdapter` is a free fallback with weaker scene control. Swapping the default provider is empirical and expected to be revisited as image models improve at text rendering.

## Video generation: fal.ai, Seedance 2.0 Fast (image-to-video)

fal.ai acts as a model router: one API surface over multiple current video models, so per-shot model selection is a parameter rather than a separate integration per vendor. Seedance 2.0 Fast was selected because it supports image-to-video with lower latency than the standard tier, and image-to-video support is a hard requirement for any model wired here. Text-to-video is never used for character shots (see [Character consistency](../README.md#character-consistency)). Motion is off by default (`static_only=True`, `--allow-motion` to opt in) since the current format is a still slideshow.

## Voice: Kokoro `am_liam` (custom YouTube cuts), Edge TTS (CLI default), ElevenLabs (opt-in)

Custom narrative cuts (`scripts/run_*_americans.py`) use local **Kokoro-82M** (`adapters/voice/kokoro.py`, voice `am_liam`, speed 1.0). It is free, punchier than Edge, and does not hit ElevenLabs caps. Long-form measures ~205 wpm — set `NARRATION_WPM=205` so shot chunking matches. CLI default remains `EdgeTTSVoiceAdapter`; ElevenLabs Liam stays available via `--elevenlabs` at 166 wpm.

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
