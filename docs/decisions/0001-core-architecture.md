# 0001 — Core architecture decisions

**Date:** 2026-07-02  
**Status:** Accepted  
**Context:** Phase 1 design — local graph skeleton, no real providers yet.

---

## 1. LangGraph over CrewAI, AutoGen, and single-vendor agent SDKs

### Decision

Use LangGraph (Python) as the orchestration layer.

### Context

The pipeline has three requirements that set it apart from a simple LLM chain:

- **Durable checkpointing.** A run can pause at a human-review gate and resume hours later, possibly in a different process. Completed nodes must not re-run on resume.
- **Non-bypassable human-in-the-loop gates.** Two approval points exist. No code path may auto-approve or skip them. The framework must make this enforceable at the architecture level, not just by convention.
- **Conditional branching with capped retries.** Each shot has a quality gate. Failure routes back to regeneration, but only up to a fixed cap; after that, the shot is escalated rather than retried indefinitely.

### Why the alternatives lost

| Option | Why it was rejected |
|---|---|
| **CrewAI** | Role-based framework. Prototyping speed is good but there is no first-class checkpointing, no interrupt/resume primitive, and retry/branching is bolted on. Would require reimplementing the durable-execution layer that LangGraph provides. |
| **AutoGen** | Conversation-centric. Multi-agent dialogue is not the shape of this problem; the work is a linear pipeline with parallel fan-out. AutoGen's execution model would be fighting the grain of the problem. |
| **Single-vendor SDKs** (OpenAI Assistants, Anthropic Claude tools) | Lock model choice. The pipeline needs per-shot model routing — cheapest model on static pans, best available on motion shots. A vendor SDK makes that a rewrite, not a config change. |
| **Custom async pipeline** | Builds the checkpointer, retry logic, and interrupt mechanism from scratch. All three are primitives in LangGraph. |

### Why LangGraph won

LangGraph's `interrupt()` / `Command(resume=...)` pattern makes the human gates first-class: the graph literally cannot proceed past the interrupt node until the caller provides a resume payload. The `MemorySaver` / `SqliteSaver` / Postgres checkpointer hierarchy lets Phase 1 run purely in-memory while Phase 3 migrates to durable storage with no changes to node logic. `Send` provides typed fan-out with a reducer-based fan-in that handles out-of-order shot completions. These are the exact three requirements above, solved directly.

---

## 2. The still-first rule is a hard invariant, not a guideline

### Decision

Every `motion` shot must have a derived still — anchored to the approved character reference sheet — before any video-generation call. This is enforced in code at two layers (validation and adapter), not documented in a prompt or README.

### Why this is an invariant and not a best practice

Current video models do not maintain character identity across independently generated clips. A text-to-video call for a character shot reinvents the character from the text description each time. Identity drift is not a rare edge case — it is the default behaviour. The result is that a narrative with three shots of "the same character" can produce three visually distinct people.

The still-first pattern breaks this by making the character's identity a **concrete artefact** (the reference sheet) rather than a **textual description**. Each shot gets a derived still generated from that sheet as an intermediate step. The video model then animates motion; it does not design the character. The consistency work is done in image space, where reference-based generation is more reliable.

Making this an invariant rather than a guideline matters because:
- A future engineer optimising for speed could reasonably remove the still step and generate video directly from the prompt. The code must reject this before the API call, not after the clip is reviewed.
- The quality gate's identity check is only meaningful if there is a reference to check against. A text-to-video shot has no anchor; the check becomes theatrical.
- Cost: video generation is the most expensive step. Catching a bypassed still-first rule before the API call avoids wasting money on a clip that will fail the identity check anyway.

### Enforcement layers

1. `graph/validation.py`: `assert_still_before_video(shot)` raises `ValueError` if a motion shot has an empty `still_url`. Called inside `process_shot` before any video-gen call.
2. `adapters/video_gen/base.py` and `mock.py`: `generate_clip` has `source_still_url` as a required parameter. The mock raises `ValueError` on empty input, mirroring what any real adapter must enforce. The signature makes it impossible to call without a still.

---

## 3. Character consistency is structural, not prompt-based

### Decision

Identity consistency across shots is enforced by pipeline structure (reference sheet → per-shot still → clip), not by writing better prompts or hoping the model converges.

### Why prompt-based consistency fails

The intuitive approach is to write a highly detailed character description and include it in every shot prompt. This fails for two reasons:

**Models ignore or drift from long descriptions.** A paragraph-length character description competes with the scene description, the motion instruction, and the model's prior distribution over how characters look. Studies and practice confirm that detailed prompts do not prevent drift across independently generated clips — they slow it down at best.

**Each call is independent.** Video and image generation APIs are stateless. The model has no memory of the previous shot. No matter how consistent the prompt, the model generates each clip from scratch, which means each clip is a fresh sample from the model's distribution conditioned on the prompt. Identical prompts produce different outputs.

### Why structural consistency works

The pipeline treats identity as an **artefact to be generated once and referenced always**, not a description to be regenerated every time.

1. `generate_character_refs` produces a model sheet: the character from multiple angles and expressions, generated as a consistent set. This sheet is human-approved and stored in state as the identity anchor for the entire run.
2. For each shot, `process_shot` derives a per-shot still from the reference sheet via the image model's reference/edit capability (e.g., "this character, in this pose and setting"). The image model holds identity; it is not reinventing the character.
3. The video model receives the still as `source_still_url` and animates motion from it. It cannot introduce a different character because it is not designing one — it is animating an existing image.
4. The `style_descriptor` field carries a persistent text descriptor including one deliberately distinctive identifying detail (e.g., "glowing amber left eye"). This is appended to every shot prompt as a redundant anchor for both the model and the identity check in the quality gate.
5. The quality gate compares each output clip against the reference sheet with a vision-capable LLM. Drift is measured and logged rather than discovered at the end of a long render.

### What this costs

One additional image-generation call per shot (the derived still). This is materially cheaper than a wasted video-generation call on a clip that fails the identity check, and far cheaper than discovering the problem at final review.

---

## Related files

- `graph/state.py` — `CharacterRefs` model: `sheet_image_urls`, `style_descriptor`, `per_shot_stills`
- `graph/validation.py` — `assert_still_before_video`
- `graph/nodes/generate_shots.py` — `process_shot` enforces the still-first sequence
- `adapters/video_gen/base.py` — `generate_clip` signature enforces `source_still_url`
- `README.md` — "Character consistency" section for the full rationale
