# Pipeline

```text
generate
  → TITLE_ANALYZED (code)
  → RESEARCHED (agent fills claims)
  → FACT_CHECKED (`qa`)
  → STORY_PLANNED / SCRIPTED (agent, channel prompts)
  → SCRIPT_QA_PASSED
  → WAIT_AUDIO (operator copies script.txt into ElevenLabs)
  → ingest-audio → PAUSES_DETECTED
  → SCENES_PROMPTED (1:1 with pause timestamps)
  → flow_prompts (only if originality_score ≥ 80 and ready_to_publish)
  → WAIT_IMAGES (operator Google Flow)
  → ingest-images → IMAGES_INGESTED
  → python -m channel assemble (imported audio + pause-timed stills)
  → youtube pack
  → READY
```

Drop-folder cut when the operator already has stills and audio:

```text
python -m channel drop --channel <mode> --title "<title>"
  → WAIT_DROP
  → put audio + `[00-00]_….jpg` stills in artifacts/<JOB_ID>/drop/
  → python -m channel assemble
  → 4K MP4 without burned captions
  → READY
```

State lives in `artifacts/<job_id>/manifest.json`. Stages are listed in `channel/job.py`.

## Isolated job tree

```text
artifacts/<JOB_ID>/
  manifest.json
  OPERATOR.md
  report.txt
  project.json
  characters.json
  locations.json
  scenes.json
  story.json
  company.json
  script.txt
  timestamps.json
  transcript.txt
  flow_prompts.txt
  thumbnail_prompts.txt
  research/seed.json
  research/claims.json
  research/sources.json
  fixtures/ + fixtures/video_specs/
  images/ drop/ audio/ thumbnail/ short/ final/ logs/
  assets/youtube/
```

Stills use index + timestamp filenames (`000_00-00-00.png`). Drop-folder stills keep the operator clock (`[00-00]_Hand-drawn_2D_doo.jpg`) in `drop/` and remap to those engine names on ingest. ZAPI FLOW serial downloads (`02_red_cabin.jpg`) remap on `ingest-images` (queue 1 = still 000) and Lanczos-upscale to 3840×2160. Isolated specs keep fixture/stills/output paths repo-relative under `artifacts/<JOB_ID>/`.

`JOB_ID` is `{slug}__{YYYYMMDD_HHMMSS}__{hex}`. Parallel agents must not write to `fixtures/` at the repo root or share a job directory.

`python -m channel init` still writes `channel/projects/<slug>/` for sequential local work. Cloud / parallel runs use `generate`.

## Resume

```text
.venv/bin/python -m channel generate --resume <JOB_ID>
```

Re-reads `project.json`. Stops at `WAIT_AUDIO` or `WAIT_IMAGES` until operator files exist. Does not invent WPM scene chunks. Prints `OPERATOR.md`.

`--force` compiles even when monetization is not ready (still do not emit `flow_prompts` unless `ready_to_publish`).

## What the agent still does

Cursor Grok is the researcher, story writer, and scene-prompt writer **after** pauses exist. Code does title parse, factcheck, originality, pause detect, drop-folder ingest, compile, YouTube pack, FFmpeg. The operator generates VO and stills outside the engine. Drop-folder cuts (`python -m channel drop`) assemble filename-clock stills without burned captions. Do not invent a third workflow.
