# What They Really Think — production system

This is the reusable engine for the YouTube channel **What They Really Think**. It is written so a Cursor Grok agent can produce a new video from a title, without editing Python. Read this fully before starting. After a cut lands, update `docs/videos/`.

The same `channel/` engine also has two other modes: `behind_the_business` (**How They Really Make Money** on YouTube; **800–2500** words) in `docs/behind-the-business.md`, and `how_they_took_over` (**How They Took Over**; **800–2500** words, ~5–15 minutes) in `docs/how-they-took-over.md`. Do **not** apply those business or takeover rules to a What They Really Think title. Pass `--channel` explicitly; do not guess the channel from the title. Cloud / parallel runs use `python -m channel generate` and write `artifacts/<JOB_ID>/`. `DO NOT MODIFY THE VIDEO ENGINE` during a normal generation task.

Sacred for every video on every channel:

- **Fresh research for every video.**
- **Different story architecture** for each company (and each WTRT title).
- **Original narration, not rewritten articles or YouTube transcripts.**
- **Unique scenes and diagrams** built around that company's actual business (or that title's actual evidence).
- Plus the existing **unique story engine** — if you could swap the names and keep the same video, throw it out.

The LangGraph HITL pipeline in `graph/` is a different product (fictional rank-POV videos). Do not route these titles through `ideate` — that node blocks real named people. This path is `channel/` → `script.txt` → imported audio → pause scenes → Google Flow stills → FFmpeg.

The **master prompt** (`channel/master_prompt.py`, exported as `MASTER` on each channel module) is the staged operator loop: title → research → `script.txt` → `WAIT_AUDIO` → timestamps → Flow prompts in batches of 20 (**Reply "next"**) → YouTube metadata. Shared look is **stick-figure doodle**; customize mood and story DNA per channel. Do not import 2nd-person explainer voice.

## The only required input

Cloud / parallel (canonical — isolated `artifacts/<JOB_ID>/`):

```text
.venv/bin/python -m channel generate --channel what_they_really_think --title "What Einstein Really Thought About Religion"
.venv/bin/python -m channel generate --channel behind_the_business --title "How Costco Really Makes Money"
.venv/bin/python -m channel generate --channel how_they_took_over --title "How Nvidia Took Over AI"
```

Sequential local (`channel/projects/<slug>/`):

```text
.venv/bin/python -m channel init "What Einstein Really Thought About Religion"
.venv/bin/python -m channel init --channel behind_the_business "How Costco Really Makes Money"
.venv/bin/python -m channel init --channel how_they_took_over "How Nvidia Took Over AI"
```

`init` defaults to `what_they_really_think`. Pass `--channel` explicitly for the other two.

When you already have the title, the narration audio, and stills with a start clock in the filename (`[00-00]_Hand-drawn_2D_doo.jpg`):

```text
.venv/bin/python -m channel drop --channel what_they_really_think --title "What Einstein Really Thought About Religion"
```

Put the files in `artifacts/<JOB_ID>/drop/`. Then `.venv/bin/python -m channel assemble <JOB_ID>`. The engine Lanczos-upscales stills to 3840×2160, cuts on those clocks (each still holds until the next; last still holds to the end of audio), and writes a YouTube-ready 4K MP4. Drop-folder cuts assemble without burned captions.

WTRT title:

```text
TITLE = "What Einstein Really Thought About Religion"
```

Optional:

```text
TARGET_DURATION          # seconds, default 600 (~10 minutes; land 5–15)
SPECIAL_INSTRUCTIONS     # tone, emphasis, things to avoid
```

Everything else is generated: who X and Y are, the relationship, research, story, narration. Scene prompts wait for the imported voice-over. The operator generates stills in Google Flow. The engine renders the MP4.

The same pipeline must work when Y is a person, a country, a religion, an ideology, a company, an idea, an event, or a group. Do not hardcode a person into `channel/config.py`. Story content lives in `channel/projects/<slug>/project.json`.

## What these videos are

Entertaining illustrated documentaries. The viewer clicks a mystery title and leaves having heard a **story that answers it**.

They must not feel like Wikipedia read aloud, a school essay, a quote list, a slideshow, or a lecture.

The storyline is a **blunt simple explanatory cartoon**. Write as if a sharp five-year-old is watching with an adult. Tiny words. Cause, then effect. Funny when the evidence is actually funny — not a roast, not baby talk, not a lecture. An adult should still enjoy it and learn the real names and dates. One idea at a time. One returning picture. **Do not read long numbers** aloud — say `about 158 billion`, not `158,359,009,867`. Exact digits stay in claims. No hiding OpenAI, Grok, SpaceX, Tesla as "the lab" or "the chatbot shop". Those names are spoken. They stay **out of image prompts**.

Each title needs a **unique story engine** — one object, one place, one reversal that would not work on any other shipped cut. Read `docs/videos/` before you write. If you could swap two names and reuse the last spine, throw it out. `lint_story.py` fails reused chapter cards, a too-close `the_thought`, and the recycled "Month Year. Name…" cold open. At most three chapters may be generic `The <Noun>` posters.

Retention contract: **question → answer → new question**, not fact → fact → fact. Every ~20–30 seconds, something new (a date, a letter, a reversal, a place). Biography is supporting material only — include it when it explains the opinion, otherwise cut it.

`the_thought` in the fixture is the **title payoff**: one sentence a child could repeat that answers the title. Say it, show it, say it again. Hook a **kid map of 5–8 steps** this title owns. Narration around it is an intelligent person telling a fascinating story to a friend — not baby talk, not a professor. Copy the grammar in `docs/video-engine/QUALITY_BAR.md`. Never copy a reference-cut spine.

Research through the day you are writing so the facts are current. **Do not say today's calendar date in the VO.** Do not say "as of today", "today is August 22", "this morning", or "ten days ago". Date events with months and years (`In August 2026`). The linter rejects production-clock phrasing.

## Architecture

| Piece | Role |
|---|---|
| `channel/modes.py` | Explicit `ChannelMode`: `what_they_really_think`, `behind_the_business`, or `how_they_took_over`. |
| `channel/config.py` | Permanent style, voice, pacing per channel mode (`CHANNEL` / `BEHIND_THE_BUSINESS` / `HOW_THEY_TOOK_OVER`). No people. |
| `channel/schema.py` | Shared `VideoProject` (research, story, bibles, scenes). Optional `business` or `takeover` block. |
| `channel/title.py` | Agent 1 — parse the title for the selected channel. |
| `channel/business_prompts.py` | How They Really Make Money stage prompts (`MASTER` + money DNA). |
| `channel/takeover_prompts.py` | How They Took Over stage prompts (`MASTER` + takeover DNA). |
| `channel/research.py` | Encyclopedia **seed** only. Agent adds primary-source claims. |
| `channel/factcheck.py` | Mechanical quote/source checks. |
| `channel/master_prompt.py` | Staged **master prompt** (`MASTER`) — same operator loop on every channel; DNA customized per mode. |
| `channel/agent_prompts.py` | What They Really Think stage prompts (`MASTER` + research → story → scenes). |
| `channel/prompts.py` | Image prompt assembler: global style + bible + action. |
| `channel/character_locks.json` | Public-figure cartoon faces; hashed photo + sheet in `channel/character_sheets/`. |
| `channel/quality_bar.py` | Cinema grammar (kid map, oversized focal object, unique stills). Spec: `docs/video-engine/QUALITY_BAR.md`. |
| `channel/drop.py` | Drop-folder cut: timestamped stills (`[00-00]_….jpg`) + audio → 4K assemble without burned captions. |
| `channel/compile.py` | Writes fixture, `script.txt`, spec (`voice: imported`), then after pauses `flow_prompts.txt` + ingest jobs. |
| `channel/youtube.py` | Description, tags, chapter stamps, honest synthetic-media disclosure, 1280×720 and 1080×1920 overlays after Flow stills land. |
| `channel/cadence.py` | 24h assemble cap between different titles. Same-slug rebuilds allowed. |
| `channel/originality_policy.py` | Permanent originality + monetization thresholds (score ≥ 80, last 10 videos). |
| `channel/originality.py` | Mass-production detector: hook / phrasing / structure / scenes / visuals / transitions / ending / thumb. |
| `channel/monetization_qa.py` | `ready_to_publish` score. Fail = do not emit `flow_prompts`. |
| `channel/research_policy.py` | Claim traceability. No invented quotes. |
| `channel/visual_policy.py` | Style lock + banned photoreal impersonation. |
| `scripts/lint_story.py` / `lint_storyboard.py` | Novelty, voice, 1:1 pause timestamps, prop/set economy, stock-AI language. |
| `scripts/lint_originality.py` | Compare this title to the last 10 shipped videos. |
| Google Flow (operator) | Stills. Paste `flow_prompts.txt`. Engine never calls Flow. |
| Imported audio (operator) | Narration. Copy `script.txt` into ElevenLabs (or any TTS). Engine never calls ElevenLabs. Shipped recuts may still use Kokoro `am_liam`. |
| `python -m channel assemble` | Drop-folder filename clocks, or pause-timed still holds, + mux imported VO. Drop-folder cuts assemble without burned captions. |

```text
TITLE
  → TITLE ANALYZER (code)
  → FRESH RESEARCH (agent + seed; primary sources first)
  → SOURCE VALIDATION (`python -m channel qa`)
  → STORY ARCHITECT (archetype from THIS evidence)
  → ORIGINALITY CHECK vs last 10 videos
  → NARRATION (`script.txt`)
  → FACT CHECK
  → WAIT_AUDIO (operator ElevenLabs → ingest-audio)
  → PAUSE DETECT (whisper / ffmpeg)
  → CHARACTER / LOCATION BIBLES + SCENE GENERATION (1:1 with pauses)
  → flow_prompts (only if originality_score ≥ 80 and ready_to_publish)
  → Google Flow + ingest-images
  → FFmpeg assemble (`python -m channel assemble`)
  → SHORT (optional second HITL pass; does not block long READY)
  → THUMBNAIL + METADATA
  → READY TO PUBLISH
```

Drop-folder cut (title + stills named `[00-00]_….jpg` + narration audio already exist):

```text
TITLE + DROP FOLDER
  → python -m channel drop --channel <mode> --title "…"
  → WAIT_DROP (operator puts audio + timestamped stills in drop/)
  → ingest (Lanczos 3840×2160; cuts from filename clocks)
  → FFmpeg assemble without burned captions
  → READY
```

## Execution checklist (mechanical)

```text
 1. Read this file + docs/videos/README.md + the last video's page
    (do not copy its spine; lint_story will fail you).

 2. .venv/bin/python -m channel init "What X Really Thought About Y"
    Optional: --instructions "..." --duration 600 --skip-seed
    Writes channel/projects/<slug>/project.json
    Cloud / parallel: python -m channel generate --channel what_they_really_think --title "…"
    (artifacts/<JOB_ID>/). Do not put a company name in a GenerateImage filename.

 3. RESEARCHER (Cursor Grok). Fill research.claims with sourced evidence.
    Never invent quotes. Flag contradictions. If evidence is thin, say so.

 4. .venv/bin/python -m channel qa <slug>
    Fix rejected claims. Do not write narration until factcheck is honest.

    5. STORY ARCHITECT + NARRATION WRITER using channel/agent_prompts.py
    800–2500 words (~5–15 minutes of imported VO), 4–6 chapter names this
    evidence owns (not The Suit / The Rocket / Walkout again), spoken English,
    title_payoff said in the VO. Unique story engine. Cold open is a
    sourced moment this title owns — never "X was born", never
    "February 2026. Name posted…". Write years as digits (1995); Kokoro
    pronounces them as years. Blunt simple spine. Speak real org/product
    names. No "today is DATE".

    6. BIBLES. Recurring people get ids + visual_lock WITHOUT historical names.
    Locations get ids. Optional signature_prop (≤ 6 scenes). When the prop
    returns it must be the SAME obvious object — high contrast, large in
    frame, not a faint mark. Named public figures must be a **recognizable
    cartoon of the real person** (face, hair, jaw, eyes, clothes they actually
    wear). Look up `channel/character_locks.json` first and reuse that lock
    plus the hashed photo and cartoon sheet in `channel/character_sheets/`
    as Google Flow references. Compile writes those paths onto ingest jobs.
    Never a generic clerk.

 7. .venv/bin/python -m channel generate --resume <JOB_ID>
    After narration QA the job is WAIT_AUDIO. Copy script.txt into ElevenLabs.
    python -m channel ingest-audio <JOB_ID> /path/to/vo.mp3

    8. Fill scenes 1:1 with timestamps.json / transcript.txt (SCENE_BREAKDOWN).
    Deliver Google Flow prompts in batches of 20. Wait for **Reply "next"**
    between batches. Do not dump every prompt in one chat block.
    Do not use `channel chunks` as the clock.

    9. .venv/bin/python -m channel qa <slug>
    If a critical score is below 8, rewrite only the weak section.
    qa also writes originality_score and monetization.ready_to_publish.
    If originality_score < 80 or ready_to_publish is false, regenerate
    the flagged stages (printed as `regenerate: hook, scenes, …`).
    Do not emit flow_prompts.

10. .venv/bin/python -m channel generate --resume <JOB_ID>
    Writes flow_prompts.txt (one [mm:ss] prompt per pause, blank line between),
    thumbnail_prompts.txt, ingest jobs, draft copy under assets/youtube/.
    Compile exits 1 if originality / monetization fails (`--force` to write anyway).

11. .venv/bin/python scripts/lint_story.py <job spec>
    Rewrite until it passes.
    Then: .venv/bin/python scripts/lint_originality.py <job spec>

12. .venv/bin/python scripts/lint_storyboard.py <job spec>

13. Paste flow_prompts.txt into Google Flow (16:9, one image per prompt).
    ZAPI serial files like `02_red_cabin.jpg` remap on ingest (queue 1 = `000_00-00-00.png`)
    and Lanczos-upscale to 3840×2160 so assemble renders a 4K long cut.
    Upload `flow_batches.txt` (one prompt per line, all stills in one file).
    python -m channel ingest-images <JOB_ID> /path/to/pngs --partial
    Thumbnail prompts: thumbnail_prompts.txt. No on-image text — type is burned later.

14. python -m channel assemble <JOB_ID>
    Long cut only. A Short is a second HITL pass and does not block long READY.
    Never two assembles at once. A different title must wait 24 hours
    (`--force` to override a recut).

15. Verify: ffprobe duration + resolution; sync.max_cut_error_ms < 20;
    spot-check frames for letterbox.
    `python -m channel youtube <slug>` writes description + tags (assemble
    stamps chapter times) and burns 1280×720 and 1080×1920 JPEG type.
    Thumbnail still: tight chest-up, FACE ≥30% of the frame, dramatic light,
    empty right third. YouTube kills loose wide shots.
    Description: search phrase in the first 200 characters, then chapters,
    then the honest synthetic-media disclosure (packer adds it). Shorts
    description is:

        Watch the full video:
        https://youtu.be/<long-video-id>

        <short_title>. <one-paragraph hook>

        Illustrated documentary. Stills and narration are generated. …

    Tick YouTube Studio's altered/synthetic content checkbox on upload.
    Cartoon work usually labels in the expanded description, not the
    photoreal player badge. Paste `assets/youtube/channel_about.txt` into
    the channel About box once.

    After the long video is live, set youtube.full_video_url and re-run
    `python -m channel youtube <slug>`.

16. Update docs/videos/<slug>.md + README.md with a "## Do not copy" list
    of quoted phrases. In the SAME change, commit the playbook files
    listed under Shared contract, plus this cut's fixtures, video_spec,
    stills modules, and docs/videos page. Other clones only
    see what is in git. Push so a new environment can `git pull`.
    Never commit assets/ or .env.
```

Equivalent: `.venv/bin/python scripts/run_title.py "What X Really Thought About Y"` (defaults to `init`).

## Voice (imported audio, in sync)

- **Engine:** operator-imported audio. Copy `script.txt` into ElevenLabs (or any TTS). The engine never calls ElevenLabs, Edge, or Kokoro on new jobs. Scene cuts come from pauses (`ingest-audio`, default 280ms). Shipped recuts may still use Kokoro `am_liam` at **1.0–1.15** (default **1.15**). **800–2500 words lands near 5–15 minutes.** Shipped older cuts may stay near 8 minutes or the old 20–25 minute budget — do not rewrite them to the new length.
- **Length:** new long cuts are **5–15 minutes**. Do not pad a lecture. Add a unique engine, more sourced reversals, and more places. Still duration is the pause interval, not a guessed 4–8 second WPM chunk.
- **Captions:** generate-path stills may burn a stylish lower-third of that scene's line. Drop-folder cuts assemble without burned captions. Continuous imported VO has no silent chapter cards. Spec field `burn_captions` (default on for generate / compile; false for `python -m channel drop`). Lines must wrap inside the frame — never shear a last line off the left or right. On 9:16 Shorts the caption sits in the **YouTube safe band** (above the like / title / music chrome, inside the side rails). Write short spoken sentences so a caption is two readable lines, not one overflowing paragraph.
- **Years:** write `1995` in the fixture and on-screen caption. Never spell the year.
- Shipped older cuts may use different speeds (leave those specs alone).
- **Sync:** pause table + faster-whisper word timestamps; `sync.max_cut_error_ms` < 20 after render.

## Pictures

- One Google Flow still per pause timestamp, from `flow_prompts.txt`.
- **Global style is frozen** in `channel/config.py` (`GLOBAL_VISUAL_STYLE`). New titles also get a per-slug palette accent so stills are not one interchangeable farm look. Shipped stills stay as generated. Agents fill action and composition only. Compile prepends the prefix.
- Flat **stick-figure doodle** animation: hand-drawn 2D, bold outlines, solid color-block backgrounds, muted historical palette on Think. Named people are a **recognizable cartoon of the real person** on that stick-figure construction. Not photoreal, not 3D, not anime.
- Historical personal names stay **out** of image prompts. Identity is the character bible `visual_lock`.
- Recurring public figures get a **distinctive cartoon lock** (hair, face, jaw, eyes, clothes) so the viewer names them. That is a **recognizable cartoon of the real person** drawn as a stick-figure doodle, not a photograph, not a cloned voice, not a generic clerk. Reuse `channel/character_locks.json` and the hashed photo plus sheet in `channel/character_sheets/` when the same person already shipped. Pass those files as Google Flow references. Compile applies the lock and writes the refs onto ingest jobs automatically. Match the **grammar** in `docs/video-engine/QUALITY_BAR.md` (kid map, one oversized focal object, unique cinema stills, punchy Short) without cloning a reference-cut spine. Person-titled cuts stay ~35–42% hero; company-titled cuts may run empty cinematic sets with costume-locked extras.
- **Hero variety:** about 35–42% hero on person titles (lint warns above 45% and below 28%). Mix crowd and empty cinematic sets. 12+ locations. Unique visual verb every still — `{SET} {who} {physical verb} {one oversized object} {named lighting}`. Do not collapse to repeating desk/binder/lobby templates or “clean business illustration of a filing table” wallpaper. Two named people in a title both appear as cartoons when the beat needs them. Signature prop in at most 6 scenes, huge and high contrast when it returns.
- Fill the frame. Cover-crop keeps the **top** of 3:2 Grok stills so on-image labels are never sheared. `ingest-images` and drop-folder ingest Lanczos-upscale stills to **3840×2160** so assemble renders 4K. Drop stills use a bracket clock (`[00-00]_….jpg`). Thumbs are **1280×720 JPEG**.
- Channel profile: **800×800** JPEG, circular crop (`python -m channel branding --profile`). Channel cover: **2560×1440** JPEG, ≤6 MB, faces in the center **1546×423** safe band (`--cover`).
- Composition changes every ~5–7 seconds on new 5–15 minute cuts. Style does not.

## The Short

One Short per long video. Not a summary. The single most surprising piece, 30–50 seconds, 9:16. First spoken sentence is the punch (≤16 words). First still is that picture. Then a reason to tap the long video. Last scene is a branded end card: **Watch the full video. The link is in the description.** (spoken + on-screen). Unique composition every shot. The YouTube Shorts **description** is different — link first, then the punch:

```text
Watch the full video:
https://youtu.be/<long-video-id>

He Summoned It Anyway. In 2014 he told MIT…
```

Long and Short descriptions end with the honest synthetic-media disclosure. Compile writes a 9:16 Shorts thumbnail job; type is burned into a 1080×1920 JPEG. Lint with `lint_story.py <spec> --short`. After assemble, open the Short and check the burned captions sit above the YouTube UI — if they hug the bottom edge, the engine safe-band has regressed.

## Originality and monetization (automatic)

Every new title is compared to the **last 10** shipped videos in
`docs/videos/README.md`. Similarity is measured on hook, phrasing (4-gram
overlap), chapter structure, scene sequence, shot-type composition,
stock transitions, ending, and thumbnail text. Brand (stick-figure doodle,
channel name, Kokoro, title pattern) is ignored. Score =
`100 − average weighted similarity`. Need **originality_score ≥ 80**.

`python -m channel qa <slug>` writes `originality` and `monetization` onto
the project. Fail conditions (do not emit `flow_prompts` / do not ingest images):

- originality_score < 80, or too close to one recent cut
- stock hook / stock transition / stock ending / generic AI phrasing
- name-swap spine (swap the people, same video)
- research/story/narration/education/retention < 8
- mass_production_risk > 3
- overall < 80 or `ready_to_publish` false

What gets regenerated: only the stages `regenerate_targets` prints
(hook, narration, chapters, scenes, ending, thumbnail). Rewrite those,
re-run qa + lint, then images.

Assemble (`run_custom_video.py`) re-checks originality unless `--force`.

## Hard invariants

- New title = new story. Never clone a shipped beat sheet. Unique story
  engine per title (new object, new place, new reversal, new chapter cards).
  **originality_score ≥ 80** vs the last 10 videos. `ready_to_publish`
  must be true before images.
- Third-person narrator. YouTube descriptions (long and Shorts) include an honest synthetic-media disclosure.
- This channel tells a history story. It does not give medical, legal, or investment advice.
- No Nazi flags/swastikas/camps/gore; no real-person photoreal faces; no cloning a real person's voice.
- Do not invent quotes or private thoughts. If the evidence cannot establish what they thought, say so in the story.
- Do not run two assemble scripts at once (`_ENCODE_CONCURRENCY = 3`).
- Different titles wait **24 hours** between assembles (same-slug rebuilds are allowed; `--force` overrides). Do not ship a new 5–15 minute cut every day from one template.
- Do not hardcode a person into the engine. Only the title changes.

## Shared contract (other clones)

Chat is not the source of truth. A new agent in a new environment starts from
**git** (`docs/custom-videos.md`, `AGENTS.md`, `.cursor/rules/custom-videos.mdc`,
`docs/videos/`, `channel/`, `scripts/lint_*.py`, shipped `fixtures/`).

If you change how these videos are made — captions, YouTube copy, voice,
length, story rules, image brands, thumbs — update **all** of these in the
same commit, then push:

- `docs/custom-videos.md` (this playbook)
- `AGENTS.md` (repo contract)
- `.cursor/rules/custom-videos.mdc` (always-on Cursor rule)
- `channel/agent_prompts.py` if a stage prompt changed
- a linter or test if the rule can be checked by a machine
- `docs/videos/<slug>.md` + `docs/videos/README.md` if a cut shipped

Do not leave a production rule only in conversation. Do not change one
surface and leave the others stale. `tests/test_channel_handoff.py` fails
when the three agent surfaces drift or a video page is missing from the
index.
