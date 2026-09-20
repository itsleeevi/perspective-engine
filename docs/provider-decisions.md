# Provider decisions

Why each dependency was chosen, what it is replacing (if anything), and where the choice will likely be revisited. Model and provider names move quickly: verify current identifiers and pricing before wiring any adapter.

There are two products. **Do not mix their providers.**

Design principle: **best tool for the role**. If a better-fit option appears, it should replace the incumbent on that product only.

## Documentary path (`channel/`) — production YouTube

This is the path that ships What They Really Think, How They Really Make Money, and How They Took Over.

| Role | Locked choice | Why |
|---|---|---|
| Stills | **Nano Banana 2** (`gemini-3.1-flash-image`) via `python -m channel images`, or operator **Google Flow** ingest | Named engine stills after QA. Character sheets as reference images. Flow remains HITL if the key is missing. Does not run on `--resume`. |
| Motion | **Omni 1.1 Flash** (`gemini-omni-1.1-flash`) via `python -m channel videos` | Opt-in image-to-video from ingested stills. Assemble prefers `videos/{still-stem}.mp4`; otherwise still holds. Does not run on `--resume`. Default remains the still slideshow. |
| Music | **Lyria 3** (`lyria-3-clip-preview`) via `python -m channel music` | Opt-in instrumental background bed. 30-second loop by default (`lyria-3.5` for a longer song). Assemble mixes `audio/music.*` under the voiceover. Does not run on `--resume`. Default remains narration-only. |
| Voice | **Gemini 3.1 Flash TTS** (`gemini-3.1-flash-tts-preview`, Charon) | Named engine TTS via `python -m channel tts`. Operator imported audio if `GEMINI_API_KEY` is missing. Shipped recuts may still use Kokoro `am_liam`. |
| Assemble | FFmpeg (`scripts/run_custom_video.py`, `scripts/run_short.py`) | Whisper-aligned still slideshow, 3840×2160 long / 1080×1920 Shorts. Omni clips loop/trim to the pause when present. |
| Research seed | Wikipedia + agent primary sources | Seed only; claims keep `claim_id` and source dates. |

Missing stills is a **hard stop** (`WAIT_IMAGES`). `python -m channel images` (Nano Banana 2 / `gemini-3.1-flash-image`) is opt-in when `GEMINI_API_KEY` is set; operator Google Flow ingest still works. `python -m channel videos` (`gemini-omni-1.1-flash`) is opt-in after stills exist and is not a silent swap from the still slideshow. `python -m channel music` (`lyria-3-clip-preview`) is opt-in after QA and is not a silent swap from narration-only audio. Missing Gemini TTS is `WAIT_AUDIO`, not a swap to Edge, ElevenLabs, or Kokoro. Do not fall back to fal.ai images, OpenAI image APIs, Edge TTS, ElevenLabs, Chatterbox, Seedance, Suno, or Udio on this path. Documentary generation does not read `FAL_KEY` or `ELEVENLABS_API_KEY`. Gemini TTS, Nano Banana 2, Omni 1.1 Flash, and Lyria 3 read `GEMINI_API_KEY`.

Specs: [`docs/video-engine/`](video-engine/), [`docs/video-engine/NARRATION.md`](video-engine/NARRATION.md), [`docs/video-engine/VISUAL_STYLE.md`](video-engine/VISUAL_STYLE.md).

## LangGraph prototype (`graph/`) — not YouTube titles

Durable code lives in `graph/`. Adapters under `adapters/` are disposable. `ideate` rejects real named people. This path is independent of `channel/`.

### Orchestration: LangGraph (Python)

Durable checkpointing, human-in-the-loop interrupts, and conditional retry/branching are first-class primitives here, not bolted on. Role-based frameworks (CrewAI) and conversation-centric frameworks (AutoGen) prototype faster but don't give the execution control this pipeline depends on; single-vendor agent SDKs would lock model choice, which conflicts with per-shot model routing (cheap model for static pans, best available for motion). Full comparison in [`decisions/0001-core-architecture.md`](decisions/0001-core-architecture.md).

### Script / shot-breakdown LLM: OpenAI, with Anthropic Claude Haiku for the per-shot quality check

Adapter-based (`adapters/llm/`), so swapping providers is a new adapter, not an orchestration change. `OpenAILLMAdapter` handles the two authoring calls (script writing, storyboard visualization); the prompt content behind both is shared verbatim with the Anthropic adapter (`adapters/llm/_prompts.py`). The vision-based quality check still delegates to `AnthropicLLMAdapter` — Claude Haiku is the cheap, adequate choice for a call that runs once per shot.

### Image generation: OpenAI `gpt-image-*` (default), Nano Banana 2, fal.ai FLUX, Pollinations (free)

Graph-only. `OpenAIImageGenAdapter` is the default on that path because it was measured to render in-scene text more reliably. `GeminiImageGenAdapter` (`--image-provider gemini-3.1-flash-image` / `nano-banana-2`) is Nano Banana 2, native 16:9, same `GEMINI_API_KEY` as documentary TTS. `FalImageGenAdapter` remains available via `--image-provider fal`. Documentary titles use `python -m channel images` or Google Flow, **not** these graph adapters as a silent swap.

### Video generation: fal.ai Seedance 2.0 Fast (default), Omni 1.1 Flash (opt-in)

Graph-only model router. Default remains Seedance (`--video-provider seedance`). `--video-provider gemini-omni-1.1-flash` / `omi-1.1-flash` is Omni 1.1 Flash image-to-video (same `GEMINI_API_KEY`). Text-to-video is never used for character shots (see [Character consistency](architecture.md#character-consistency-in-depth)). Motion is off by default (`static_only=True`, `--allow-motion` to opt in). Documentary titles use `python -m channel videos`, **not** these graph adapters as a silent swap.

### Voice: Edge TTS default, ElevenLabs opt-in, Chatterbox isolated venv

Graph CLI default remains `EdgeTTSVoiceAdapter`. ElevenLabs is opt-in via `--elevenlabs`. Chatterbox-Turbo lives in an isolated `.venv-tts` for that prototype. **None of these are allowed on `channel/` documentary assemble.**

### Assembly: FFmpeg today, Remotion planned

The graph `assemble` node downloads fal.ai-hosted assets, converts static-pan stills into segments, concatenates, and mixes voiceover via ffmpeg. Remotion is the planned replacement on that product once captions and motion graphics are needed. Documentary assemble is a different script path (`scripts/run_custom_video.py`).

## Planned, not yet wired (LangGraph only)

These appear in [`docs/roadmap.md`](roadmap.md) because the local-prototype phase intentionally defers paid/managed infrastructure until the core control flow is proven:

- **Observability: LangSmith.** Tracing of every node call, retry, and interrupt.
- **Backend: FastAPI.** Already used for the review UI (`webui/`); may grow into the full API service.
- **Compute: Modal.** Serverless functions per stage.
- **State / persistence: Neon (serverless Postgres).** Replaces local SQLite/in-memory checkpointer.
- **Object storage: Cloudflare R2.** State already stores asset URLs rather than binaries.
- **Review UI: Next.js.** Fuller dashboard than the current FastAPI + static-HTML review UI.
- **Publishing: YouTube Data API v3.** Rate-limited in code once wired; `publish` already enforces the cadence cap against mock output today.

Documentary YouTube copy is already written by `python -m channel youtube` (description, tags, thumbs, synthetic-media disclosure). That is not this roadmap item.
