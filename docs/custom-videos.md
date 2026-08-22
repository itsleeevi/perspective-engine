# Custom narrative videos — the system

This is the reusable production system for the one-off YouTube cuts. It is written so a cheap execution model (Cursor grok 4.6 class) can produce a new video end-to-end by following it mechanically. Read it fully before starting. After a cut lands, update `docs/videos/`.

## What these videos are

**Perspective-shift short films made of still images.** The viewer spends five minutes inside the hero's mental model of something (a country, a war, a rival) and leaves having learned how that model worked and where it was a cartoon. Teaching happens through dramatic irony — we know more than he did and we watch him act on the wrong picture — never through a numbered lecture.

**Explain the thought as if the watcher were five.** Not baby talk. Not a lecture. One sentence a child could repeat out loud, then a story that makes that sentence visible in every chapter. Assume the viewer does not know the history, the treaties, or the dates. Name what was in the hero's head in small words, pick **one** simple metaphor, and keep returning to it. Clever metaphors that need a second translation have failed. If a smart adult still cannot say the thought in one breath after the cold open, rewrite.

### The teaching contract (`the_thought`)

The watcher is not a historian. After thirty seconds they must be able to answer: **what did he believe, in small words?** Write that sentence *before* the beat sheet. Put it in the fixture as `the_thought` (max 22 words). `scripts/lint_story.py` fails the cut if it is missing or not said in the VO.

Formula: `He thought [simple if] [simple then].` Cause and effect a five-year-old could act out with toys.

| | |
|---|---|
| Good | `He thought if he was nice to a bad man, the bad man would leave him alone.` |
| Bad | `He thought he had put a storm on a leash.` — needs decoding |
| Bad | `He misread the pact as a durable security architecture.` — Wikipedia |
| Bad | a list of facts the hero "didn't know" — that is a lecture |

How the film uses it:

1. **Say it** in the cold open (the hook *is* the sentence, or the sentence is the first line after the hook).
2. **Show it** in every chapter as one piece of the idea (being nice / sharing / smiling / the scary man going away). Teach by pictures of the belief, not by dates.
3. **Say it again** on the button, then one short line of what actually happened.

Do not assume the viewer already knows the event. You may *picture* a date or a paper (`two in the morning, they sign a paper`) but the lesson never depends on recognizing the name of that paper. One idea. If you need a second sentence to explain the first, the first failed. A Short uses the same `the_thought`; it does not invent a cleverer one.

If a cut could be a Wikipedia list with pictures, it failed. The engine of every story: **want → the substitute he preferred to reality → the crack he refused to see → reality walks in → price.**

## The writers' room (do this BEFORE any code or images)

Write the film as a film. Work in this order, and do not skip stages:

1. **Logline.** One sentence with an irony in it. ("A man declares war on a country he has only ever read about, and loses to the difference.")
2. **Beat sheet (Save-the-Cat compressed).** Cold open image → setup of the want → the substitute world he builds (fun and games) → midpoint crack (he almost sees the truth) → he doubles down → reality arrives (all is lost) → price → button that restates the mechanism in one line. 5–7 sequences, each gets a black chapter card with a poster-like two-or-three-word name.
3. **Scene list.** Every scene is a *place + something happening*, not a concept. A scene can hold 8–20 narration chunks. Consecutive scenes must connect (consequence, match cut, or time jump — "and so / but then", never "and then also").
4. **Prop economy.** Choose ONE signature prop. It appears in the setup, at act turns, at the climax, and in the last shot — **about 5–6 scenes total, never more**. The v4 Hitler cut put the book in half the frames and it read as a screensaver. Everything else in frame changes scene to scene: new places, new faces, new objects. Declare the budget in the stills module (`PROP_BUDGET = {"THE BOOK": 6}`) — the linter enforces it.
5. **Narration prose.** Third person, spoken English: contractions, questions to the viewer, long sentences that land on short ones. Periods are punches, not list items — never telegram fragments ("Soft cover. German. A boy's book."), never "fake number one", never narrator-"I". Read every paragraph aloud once; anything you stumble on, rewrite.
   Put `the_thought` in the fixture: one sentence a five-year-old could repeat. The narration must contain that sentence (the linter checks). Say it in the cold open or right after, show it in the middle, say it again on the button. Do not hide the thought inside a metaphor the viewer has to decode.
6. **Chapter names.** 4–6, silent black cards, white type (`title_style: "chapter"`, `speak_title_cards: false`). The card is a breath, not a read-aloud heading.

Story quality gate: before proceeding, check the beat sheet against `docs/videos/` — if any sequence rhymes with a shipped cut (five fakes, plane clap, coupon, two Americas), rewrite that sequence.

### Story generation with a cheap model (the loop that makes it work)

A grok-4.6-class model writes a good script only when the job is staged and the output is machine-checked. Never ask it to "write the video" in one prompt. Run these stages as separate steps, keeping only the output of each:

1. **Research one true anchor.** Find 3–5 verifiable, *concrete* facts about the subject (an object, a date, a quote, a room). Pick the single most cinematic one as the cold-open image. A story hangs on one true thing, not on a summary.
2. **Three loglines, keep one.** Generate three one-sentence loglines, each with a different irony. Pick the one where the hero's mental model does the most damage. Discard the others entirely — do not blend.
3. **Beat sheet.** Expand the winner into the 8-stage sheet from above (cold open → want → substitute world → midpoint crack → double-down → reality arrives → price → button). Each stage: 2–3 sentences of what happens *on screen*, plus which chapter it lives in.
4. **Scene list.** Turn the sheet into 12–20 scenes, each a place + an event, each connected to the previous by "and so / but then" (write the connective down; if it is "and then also," merge or cut the scene).
5. **Prose.** Write the narration one chapter at a time in spoken English, as if explaining the hero's thought to a five-year-old who is still watching a movie. Read-aloud test per paragraph. Put `the_thought` in the fixture JSON and in the narration.
6. **Lint, then loop.** `scripts/lint_story.py` checks novelty against every shipped fixture (4-gram overlap), the do-not-copy motif lists in `docs/videos/`, third-person voice, spoken register, chapter structure, and that `the_thought` is actually said. Rewrite until it passes — the write → lint → rewrite loop is what makes a cheap model's script shippable, not the first draft.

## Voice (free, human, in sync)

- **Engine:** custom cuts prefer Kokoro `am_michael` at speed **0.90** with short pauses (storyteller who still moves). Chatterbox-Turbo (`adapters/voice/chatterbox.py`, `.venv-tts`) is the more natural engine when cloning works; on this CPU, cloning a reference clip dies on float64, so do not block a cut on it. Never Edge, never ElevenLabs.
- **Fallback:** Kokoro `am_liam` (speed 0.80, `NARRATION_WPM=175`) if Michael is wrong for the title.
- **Sync is engine-independent:** the worker force-aligns the rendered audio with faster-whisper word timestamps; `_align_word_offsets` + `split_run_durations` turn those into exact per-shot durations. Any engine that can produce a wav gets the same measured sync. Cuts land in pauses; the assemble metadata (`sync.max_cut_error_ms`) must stay under ~20 ms — check it after every render.
- Chunking WPM in the spec must match the measured voice (~175 for both Chatterbox-Turbo defaults and Kokoro 0.80). Probe a paragraph of real story prose, not a slogan, before a full render.
- **Naturalness knobs** (all in `adapters/voice/chatterbox.py`): sampler temperature 0.9 by default (`CHATTERBOX_TEMPERATURE`; 0.7 turns newsreader, 1.0+ wanders); a ~0.3s **breath** of real silence between packs (`CHATTERBOX_BREATH`) so thoughts don't slam into each other; whole-track loudness normalised to -16 LUFS. Narration may use sparse Chatterbox paralinguistic tags — `[sigh]`, `[chuckle]` — at most a handful per video, only where a human narrator would actually react; they are stripped from word counts automatically so sync holds.

## Pictures

- One Grok still per narration chunk, generated from `fixtures/<prefix>image_jobs.json` at 16:9 by GenerateImage subagents (batches of ~16).
- Locked look: same hero (say "SAME" in every prompt), no readable text, no Nazi/extremist symbols, no photoreal celebrity faces, historical names OUT of image prompts (safety blocks).
- **Look is per title.** The Stalin–Hitler v4 cut uses a Simple History-like **flat 2D vector** explainer (dot eyes, solid colors, red-to-orange portrait gradients, paper-cutout scenes) — not painterly cinema. Matching that look does **not** mean copying a Wikipedia biography: the pictures can be educational; the story must still be the hero's thought.
- Fill the frame: cover-crop to 16:9 on ingest; thumbs are **1280×720 JPEG** top-cropped from the 3:2 master.
- Cinema, not slides: flatlays/symbolic graphics ≤ 25% of shots; ≤ 3 consecutive shots in one set; hero absent from long stretches. The linter enforces all of this.

## The Short (every long video ships with one)

Each long video gets a vertical companion Short whose only job is **driving traffic to the long video**. It is not a summary and not a trailer reel — it is a 25–45 second open loop:

- **Structure:** the story's single most ironic concrete image in the first two seconds (no greeting, no context) → two or three escalating beats *inside the hero's head* → stop right BEFORE the payoff → spoken CTA as the last line ("The full story is on this channel."). Never resolve the irony; never spoil the long video's ending or its button line.
- **Data:** a `"short"` block in the video spec (fixture, stills module, still_prefix, stills_dir, output). The short fixture uses the normal schema with `include_level_titles: false` and 60–135 words of narration. 8–12 stills at **9:16**, same hero look and style prefix as the long video so the click feels continuous.
- **Tools:** same cheap-model loop — write, then `lint_story.py <spec> --short` (length, CTA present, no banned motifs; overlap with its own long fixture is allowed), `lint_storyboard.py <spec> --short`, `make_image_jobs.py <spec> --short` (jobs carry `aspect: 9:16`), then `scripts/run_short.py <spec>` renders 1080×1920 with the same whisper-aligned voice and drift-free cuts. Upload with the long video's link pinned in the comment and the same title phrasing.

## Execution checklist (mechanical — follow in order)

```text
 1. Read this file + docs/videos/README.md + the last video's page.
 2. Write fixtures/video_specs/<slug>.json (topic, fixture, stills_module,
    still_prefix, stills_dir, thread_id, voice, narration_wpm).
 3. Writers' room (above): staged story generation, one stage per step.
    Produce: fixture JSON (hook + levels + **the_thought**, title_style /
    speak_title_cards set) and narration prose inside it. the_thought must
    be a sentence a child could repeat, and it must appear in the VO.
 4. .venv/bin/python scripts/lint_story.py fixtures/video_specs/<slug>.json
    → rewrite the narration until it passes (novelty, motifs, voice).
 5. Write fixtures/<slug>_stills.py: STILLS list (shot_type, who, scene),
    PROP_BUDGET, SET_TOKENS, prompt_for(). One scene per chunk — get the
    chunk list with split_beat_into_chunks at the spec's NARRATION_WPM.
 6. .venv/bin/python scripts/lint_storyboard.py fixtures/video_specs/<slug>.json
    → fix every ERROR, repeat until it passes.
 7. .venv/bin/python scripts/make_image_jobs.py fixtures/video_specs/<slug>.json
 8. Generate stills with GenerateImage subagents in ranges of ~16 jobs,
    16:9, exact prompt text; on safety block retry once without
    historical-person wording.
 9. .venv/bin/python scripts/run_custom_video.py fixtures/video_specs/<slug>.json
    (never two assembles at once; 4K encode is CPU-bound).
10. Verify: ffprobe duration + resolution; sync.max_cut_error_ms < 20 in the
    output JSON; spot-check 4-6 frames for black bars.
11. Thumbnail (1280×720 JPEG) + description (search phrase in first 200
    chars, chapters at the black cards, disclosure line).
12. The Short: add the "short" block to the spec; write
    fixtures/<slug>_short.json + fixtures/<slug>_short_stills.py; then
    lint_story --short → lint_storyboard --short → make_image_jobs --short →
    generate 9:16 stills → scripts/run_short.py <spec>.
13. Update docs/videos/<slug>.md + README.md — including its "## Do not copy"
    section (quoted phrases there feed lint_story's banned-motif check).
    Commit code+docs only when asked. Never commit assets/ or .env.
```

## Hard invariants (unchanged)

- New title = new story. Never clone a shipped beat sheet.
- Third-person narrator. Synthetic-content disclosure always on.
- No Nazi flags/swastikas/camps/gore; no real-person photoreal faces; no cloning a real person's voice.
- Do not run two assemble scripts at once (`_ENCODE_CONCURRENCY = 3`).
