# Roadmap

The build is sequenced to defer paid and managed infrastructure until the core control flow is proven and covered by tests. See `AGENTS.md` for the current phase and what's explicitly out of scope until it's complete.

## Phase 1: local only (current)

Full state schema, node logic, and control flow (fan-out, retry, interrupts), running locally with an in-memory or SQLite checkpointer, local-filesystem assets, and both mocked and real (but cheap) model calls behind adapters. No managed database, object storage, serverless compute, or tracing. The goal is correct, tested control flow; see [Implemented Today](../README.md#implemented-today) for what's already true.

## Phase 2: one real video, still local

Real providers behind every adapter (already wired: Anthropic, fal.ai FLUX + Seedance, ElevenLabs), the full graph triggered from the CLI or browser UI to produce a single end-to-end video, both review gates approved interactively. Includes an empirical image-model A/B for the character-consistency role: the model that best holds a locked identity across pose and scene changes wins, decided by evidence rather than default choice.

## Phase 3: durable infrastructure

- Migrate the checkpointer from SQLite to Postgres (Neon) so runs survive process restarts and can be resumed from any machine.
- Migrate generated assets from local disk to Cloudflare R2; state already stores URLs, not binaries, so this is a storage-backend swap.
- Replace the lightweight FastAPI review UI with a full Next.js dashboard.
- Move compute to serverless functions per stage (Modal), suited to bursty parallel shot generation.
- Enable LangSmith tracing across every node call, retry, and interrupt.

## Phase 4: scheduling

Automated triggers for the steps suitable for automation (e.g. scheduled topic ideation, batch shot generation), within the publish-cadence cap that's already enforced in code (`graph/config.py::PUBLISH_CADENCE_SECONDS`), plus controlled YouTube publishing via the Data API v3.

## Out of scope until Phase 1 is complete

No real provider APIs beyond what's already wired for Phase 2 validation, no managed database / object storage / serverless / tracing configuration, no production review UI, and no publish or scheduling integration.
