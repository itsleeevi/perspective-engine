# Architecture

YouTube documentaries are the `channel/` engine ([`docs/video-engine/`](video-engine/), [`AGENTS.md`](../AGENTS.md)). This file is the deep-dive for the separate LangGraph skeleton in `graph/`. For that prototype's flowchart, see the [Workflow diagram](../README.md#workflow) in the README.

## State

`graph/state.py` defines `PipelineState`, a single typed Pydantic object threaded through every node. Nodes read the full state and return a partial update; there are no ad hoc dictionaries passed between nodes.

- `topic`, `brief`: the run's subject and a one-sentence framing, set by `ideate`.
- `max_shots`, `static_only` (default `True`), `script_fixture_path`, `max_levels`, `include_hook`, `target_minutes`, `hero_career_progression`, `output_height`: run-configuration inputs, all settable from the CLI. `static_only` defaults to `True` because the current format is a still slideshow, not motion video; `script_fixture_path` lets a reviewed JSON fixture (`graph/script_fixture.py`) replace the script LLM call entirely, either explicitly or auto-resolved from the topic.
- `script: list[str]`: scene beats. On the LLM path beat `[0]` is the hook (unless `include_hook` is `False`); on the fixture path, beats are `[TITLE] Level N: Name` cards interleaved with narration paragraphs.
- `shot_list: list[Shot]`: per shot, an `id`, `prompt`, `duration_seconds`, `mode` (`motion` or `static_pan`, the primary cost lever), `assigned_model`, `narration` (the beat it illustrates), `is_title_card`, `still_url`, `clip_url`, `status`, `retry_count`, `manual_regen_count`, `escalated`, `quality_failure_reason`. Uses a custom `_merge_shots` reducer so fan-out updates from parallel `process_shot` executions merge back into one list, keyed by shot `id`, order-preserving.
- `character_refs: CharacterRefs`: `sheet_image_urls` (the reference sheet), `style_descriptor` (persistent text anchor with a distinctive identifying detail), `per_shot_stills` (derived still URLs keyed by shot id).
- `voiceover_url`, `music_url`, `final_video_path`: final asset pointers.
- `metadata: Metadata`: `title`, `description`, `tags`, `thumbnail_url`, and `synthetic_content_disclosure` (invariant: always `True` by the time `publish` runs).
- `cost_log: list[CostEntry]`: running spend per node, accumulated with `operator.add`.
- `human_edits_log: list[HumanEdit]`: every edit applied at a review gate, for audit.
- `last_published_at`: ISO timestamp stored in state (not external state) so the publish-cadence cap is testable by injecting a clock.

## Nodes, in order

1. **`ideate`**: validates the topic (rejects real, named, identifiable people via `assert_no_real_person`) and synthesizes a one-sentence brief.
2. **`write_script`**: produces the scene-beat script. If `script_fixture_path` resolves (explicit or auto-detected from the topic), beats are loaded from the JSON fixture at `$0` cost instead of calling the LLM (`graph/script_fixture.py`).
3. **`shot_breakdown`**: turns the script into the shot list and assigns a model per shot. A script carrying `[TITLE]` beats (i.e. any fixture-driven script) is broken down deterministically and locally, at `$0`; title beats become local title-card shots (`local-title-card`, rendered by `graph/title_cards.py`, no image-model call) and narration beats get durations derived from word count. Otherwise the LLM proposes the breakdown.
4. **`human_review_script`**: **interrupt.** Pauses for approval or inline edits before any paid generation call. Raises if rejected; no auto-approve path exists.
5. **`generate_character_refs`**: generates the reference sheet and style descriptor; the identity anchor for the run.
6. **`dispatch_shots` → `process_shot` (×N, fan-out via `Send`)**: one sub-execution per shot. Each `process_shot` run derives a still from the reference sheet, animates it (motion shots only), runs the quality/identity check, and retries internally up to `MAX_SHOT_RETRIES` before marking the shot `approved` or `escalated`.
7. **Fan-in**: a fixed (non-conditional) edge from `process_shot` to `human_review_images`. Because the edge count is deterministic (equal to the number of `Send`s dispatched), LangGraph's barrier semantics guarantee the image-review gate runs exactly once, after every shot finishes, regardless of completion order.
8. **`human_review_images`**: **interrupt.** Reviewer inspects generated stills and may regenerate flagged shots (capped at `MAX_MANUAL_REGENERATIONS` per shot) before voiceover. Regeneration happens inside the node so the fan-in barrier is untouched. Raises if rejected; no auto-approve path exists.
9. **`generate_voiceover`**: TTS narration aligned to the approved script.
10. **`assemble`**: downloads shot assets, converts stills to video segments, concatenates in order, mixes in narration via FFmpeg. Writes `final_video_path` and a JSON manifest.
11. **`generate_metadata`**: title, description, tags, thumbnail; sets the disclosure flag.
12. **`human_review_final`**: **interrupt.** Final approval before publish; same non-bypassable contract as gate 1.
13. **`publish`**: enforces the disclosure-flag invariant and the publish-cadence cap before recording `last_published_at`.

## Why the retry loop lives inside `process_shot`, not as a graph edge

A conditional edge from a quality-check node back to shot generation would fire the fan-in barrier after the *first* shot reaches a terminal state, not after all of them. Keeping the retry loop internal to the `process_shot` sub-execution keeps the barrier count exactly equal to the number of dispatched shots, the canonical LangGraph map-reduce pattern (fixed edge count equals a deterministic barrier). See `graph/graph.py` and `graph/nodes/generate_shots.py` for the implementation notes.

## Character consistency, in depth

1. **Reference sheet.** `generate_character_refs` produces a model sheet: the character from multiple angles/expressions, generated as one consistent set (the technique traditional animation uses to keep characters on-model). Human-approved implicitly as part of the script review gate's shot list, and stored as the identity anchor for the run.
2. **Image-to-video, never text-to-video.** Every `motion` shot is derived first: a per-shot still is generated from the reference sheet via the image model's image-to-image conditioning, then the video model animates *that still*. The video model never designs a character from text; it only animates an existing image.
3. **Identity check in the quality gate.** Each generated shot is compared against the reference sheet by a vision-capable LLM call. Failures are capped and retried; drift is a measured, logged property of the run, not an end-of-run guess.
4. **Persistent style descriptor.** `character_refs.style_descriptor`, including one deliberately distinctive identifying detail, is appended to every shot prompt, giving both the generation call and the identity check a concrete, redundant anchor.

The rationale for *why* this is structural rather than prompt-based (and why prompt-based consistency reliably fails) is in [`docs/decisions/0001-core-architecture.md`](decisions/0001-core-architecture.md).

## Invariants

Enforced in code (`graph/validation.py`, `graph/nodes/publish.py`), not just documented:

- No real, named, identifiable people as video subjects, validated at `ideate`.
- Every `motion` shot has a derived still before any video-generation call, validated at two layers: `graph/validation.py::assert_still_before_video` and the video adapter's required `source_still_url` parameter.
- Every shot defaults to `static_pan` (the cheap path); `motion` is opt-in per shot.
- Per-shot retries are capped at `MAX_SHOT_RETRIES` (`graph/config.py`), then escalate to human review: never an infinite loop, never a silent drop.
- The synthetic-content disclosure flag must be `True` before `publish` runs.
- Publish is rate-limited to once per `PUBLISH_CADENCE_SECONDS` (`graph/config.py`), enforced inside the `publish` node itself regardless of caller.
- Human-review interrupts (`human_review_script`, `human_review_images`, `human_review_final`) are non-bypassable: they use LangGraph's `interrupt()` primitive, which halts execution until an explicit `Command(resume=...)` is provided. No code path can auto-approve or skip them.
