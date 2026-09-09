# Quiet Wealth — production system

This is the playbook for the YouTube channel **Quiet Wealth**. Internal mode is `wealth_pov`. It reuses the shared `channel/` video engine (imported audio, Google Flow stills, assemble, originality, Shorts, YouTube pack). It is **not** a documentary channel. Do not apply What They Really Think portraits, How They Really Make Money unit economics, or How They Took Over flywheels. Do not use stick-figure doodle construction.

Read this fully before starting a Quiet Wealth cut. After a cut ships, update `docs/wealth/<slug>.md` and `docs/wealth/README.md`.

The staged operator loop is the **v5 master prompt** in `channel/wealth_prompts.py` (`MASTER`), sourced from `channel/wealth_pov_master_v5.txt`.

## Channel mode

```text
CHANNEL_MODE = wealth_pov
```

Always pass it. Do not detect the channel from the title alone.

```text
.venv/bin/python -m channel generate --channel wealth_pov --title "POV: You Stopped Trying to Look Successful"
.venv/bin/python -m channel init --channel wealth_pov "POV: You Stopped Trying to Look Successful"
```

Cloud / parallel runs must use `generate` (writes `artifacts/<JOB_ID>/`). `init` is sequential local only.

Aliases: `quiet_wealth`, `wpov`, `pov_wealth`, `longform_wealth_pov`.

Config lives in `channel/config.py` as `WEALTH_POV` / `config_for("wealth_pov")`. Stage prompts live in `channel/wealth_prompts.py`. Title parsing lives in `channel/wealth_title.py`.

## Core promise

Place the viewer inside ordinary money decisions and show how those choices change a life over time. Quiet wealth, social pressure, the wish to look successful, financial security, work, relationships, and having more choice over your time.

Default is a **fictional illustrative story**, labeled as such in the description. Not personalized financial advice.

## Sacred rules

1. **Fresh story for every video** (and fresh research for any real claim).
2. **Different story architecture** for each title.
3. **Original narration, not rewritten articles or YouTube transcripts.**
4. **Unique scenes** built around this life's places and object.
5. **unique story engine** — one object / place / reversal that would not work on any other cut.

If you could swap the lunch tin for another object's cameo and keep the same video, throw it out.

## Length and voice

- Target **about 30 minutes** (28–32 minutes; 1680–1920 seconds, target 1800).
- Script **4,500–4,800 words** at about 150–160 wpm. Aim near 4,650 if pace is unknown.
- Second person. Present tense within each scene. Very simple words.
- Six named chapters / levels inside one continuous story. Spoken level labels are allowed.
- New shot every **8–9 seconds** after the recording exists (planning midpoint 8.5s).
- Subtitles follow the voice as a separate layer. Quiet jazzy piano under the narration.
- New jobs use imported audio. Shipped recuts may stay on Kokoro `am_liam` at **1.0–1.15** (default **1.15**).
- **Do not read long numbers** aloud.

## Visual identity

`WEALTH_POV_VISUAL_STYLE`: detailed colored 2D story illustrations, complete cartoon bodies, lived-in rooms, muted natural colors, soft cel shading. Not stick-figure doodle, not empty-paper silhouettes, not photoreal, not 3D, not anime.

Fill the canvas edge to edge. Keep the lower subtitle area uncluttered but illustrated. Camera moves (PUSH / PULL / DRIFT / HOLD) are editor notes, not baked into the still.

## Pipeline

```text
 1. Read this file + docs/wealth/README.md.
 2. .venv/bin/python -m channel generate --channel wealth_pov --title "<POV title>"
 3. Fill project.wealth (ledger, characters, object) and script.txt (~4,500–4,800 words).
 4. python -m channel qa <JOB_ID>
 5. WAIT_AUDIO — copy script.txt into ElevenLabs. ingest-audio.
 6. Group the recording into 8–9 second shots. Flow prompts in batches of 20
    (Reply "next"). originality_score ≥ 80 and ready_to_publish first.
 7. ingest-images, then assemble. Drop-folder cuts assemble without burned captions.
 8. python -m channel youtube <slug>
 9. Update docs/wealth/<slug>.md and docs/wealth/README.md.
```

`DO NOT MODIFY THE VIDEO ENGINE` during a normal generation task.
