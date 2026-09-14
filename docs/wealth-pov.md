# Quiet Wealth — production system

This is the playbook for the YouTube channel **Quiet Wealth**. Internal mode is `wealth_pov`. It reuses the shared `channel/` video engine (imported audio, Google Flow stills, assemble, originality, Shorts, YouTube pack). It is **not** a documentary channel. Do not apply What They Really Think portraits, How They Really Make Money unit economics, or How They Took Over flywheels. Do not use stick-figure doodle construction.

Read this fully before starting a Quiet Wealth cut. After a cut ships, update `docs/wealth/<slug>.md` and `docs/wealth/README.md`.

The staged operator loop is the **v13 celebrity and life POV master prompt** in `channel/wealth_prompts.py` (`MASTER`), sourced from `channel/wealth_pov_master_v13.txt`. Canonical style blocks live in `channel/life_pov_blocks.py`.

## Channel mode

```text
CHANNEL_MODE = wealth_pov
```

Always pass it. Do not detect the channel from the title alone.

```text
.venv/bin/python -m channel generate --channel wealth_pov --title "POV: You Stopped Trying to Look Successful"
.venv/bin/python -m channel generate --channel wealth_pov --title "POV: You Are Cristiano Ronaldo From Age 13 to 41"
.venv/bin/python -m channel init --channel wealth_pov "POV: You Stopped Trying to Look Successful"
```

Cloud / parallel runs must use `generate` (writes `artifacts/<JOB_ID>/`). `init` is sequential local only.

Aliases: `quiet_wealth`, `wpov`, `pov_wealth`, `longform_wealth_pov`, `life_pov`, `celebrity_pov`.

Config lives in `channel/config.py` as `WEALTH_POV` / `config_for("wealth_pov")`. Stage prompts live in `channel/wealth_prompts.py`. Title parsing lives in `channel/wealth_title.py`.

## Core promise

Create an entertaining illustrated life journey that makes the viewer feel they are living through changing circumstances. A title may be an original fictional premise or a sourced real-person span. Money can create stakes, but so can belonging, ability, rivalry, creativity, recognition, control, relationships, responsibility, failure, reinvention and time.

Default for `POV: You [choice]` is a **fictional illustrative story**. `POV: You Are [Name] From Age X to Y` is a **REAL_PERSON** episode and needs verified biography. Pictures use original cartoon stand-ins either way. Not personalized financial advice.

## Sacred rules

1. **Fresh research for every video** (and a claims register for every decisive real-person claim).
2. **Different story architecture** for each title.
3. **Original narration, not rewritten articles or YouTube transcripts.**
4. **Unique scenes** built around this life's places, wardrobe tokens, and period.
5. **unique story engine** — one object / place / reversal that would not work on any other cut.

If you could swap the subject and keep the same video, throw it out.

## Length and voice

- Target **32–36 minutes**, near 34 (1800–2160 seconds, target 2040). At least 30 minutes of genuine narration.
- Script **5,600–5,800 words** at a disclosed 165–175 wpm when no voice sample exists.
- Second person. Present tense within each scene. Clear everyday English. No em dash character.
- Roughly 8–10 substantial eras. Spoken level labels are off unless requested.
- Meaning-first shots: ordinary stills usually **4–7 seconds**.
- New jobs use imported audio. Shipped recuts may stay on Kokoro `am_liam` at **1.0–1.15** (default **1.15**).
- **Do not read long numbers** aloud. Write numbers as words in the clean script.

## Visual identity

`WEALTH_POV_VISUAL_STYLE` is the v13 Section 0 lock: detailed 2D narrative cartoon, slightly enlarged heads with complete natural bodies, muted colors, restrained cel shading, one focal point. Visible protagonist skin is flat pure white `#FFFFFF`. Default cast is original non-identifying stand-ins. Fill every edge, including the bottom. No reserved subtitle space. Not stick-figure doodle, not empty-paper silhouettes, not photoreal, not 3D, not anime.

Camera moves (PUSH / PULL / DRIFT / HOLD) are editor notes, only when requested, never baked into the still.

## Scene batches

A scene request produces exactly two files:

```text
batch_NN_image_prompts_[slug].txt
batch_NN_scene_placement_[slug].txt
```

Placement line: `[ID] IMAGE: ... SHOW FROM: "..." KEEP UNTIL: "..."`.

Prove anchors with `python -m channel validate-scenes SOURCE PROMPTS PLACEMENT LEDGER`. Normally 20 scenes. "All remaining" finishes every leftover batch. After `originality_score ≥ 80` and `ready_to_publish`, concatenate prompts into `flow_prompts.txt`.

## Pipeline

```text
 1. Read this file + docs/wealth/README.md.
 2. .venv/bin/python -m channel generate --channel wealth_pov --title "<POV title>"
 3. Fill project.wealth (ledger or claims.json) and script.txt (~5,600–5,800 words).
 4. python -m channel qa <JOB_ID>
 5. WAIT_AUDIO — `python -m channel tts` (Gemini 3.1 Flash TTS) or copy script.txt into ElevenLabs. ingest-audio.
 6. Map the selected transcript with meaning-first 4–7 second shots. Two-file
    batches of 20 (Reply "next", or all remaining). originality_score ≥ 80 first.
 7. ingest-images, then assemble. Drop-folder cuts assemble without burned captions.
 8. python -m channel youtube <slug>
 9. Update docs/wealth/<slug>.md and docs/wealth/README.md.
```

`DO NOT MODIFY THE VIDEO ENGINE` during a normal generation task.
