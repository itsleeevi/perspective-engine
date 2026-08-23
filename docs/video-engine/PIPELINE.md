# Pipeline

```text
generate
  → TITLE_ANALYZED (code)
  → RESEARCHED (agent fills claims)
  → FACT_CHECKED (`qa`)
  → STORY_PLANNED / SCRIPTED (agent, channel prompts)
  → SCRIPT_QA_PASSED
  → VISUAL_PLAN_CREATED (bibles + scenes 1:1 with chunks)
  → compile into artifacts/<job_id>/
  → GenerateImage (only if originality_score ≥ 80 and ready_to_publish)
  → Kokoro + FFmpeg (`scripts/run_short.py`, `scripts/run_custom_video.py`)
  → youtube pack
  → READY
```

State lives in `artifacts/<job_id>/manifest.json`. Stages are listed in `channel/job.py`.

## Isolated job tree

```text
artifacts/<JOB_ID>/
  manifest.json
  report.txt
  project.json
  characters.json
  locations.json
  scenes.json
  story.json
  company.json
  script.txt
  research/seed.json
  research/claims.json
  research/sources.json
  fixtures/ + fixtures/video_specs/
  images/ audio/ thumbnail/ short/ final/ logs/
  assets/youtube/
```

GenerateImage uses each job’s `generate_filename` (hashed, no company words). Copy onto `filename` before assemble. Isolated specs keep fixture/stills/output paths repo-relative under `artifacts/<JOB_ID>/`.

`JOB_ID` is `{slug}__{YYYYMMDD_HHMMSS}__{hex}`. Parallel agents must not write to `fixtures/` at the repo root or share a job directory.

`python -m channel init` still writes `channel/projects/<slug>/` for sequential local work. Cloud / parallel runs use `generate`.

## Resume

```text
.venv/bin/python -m channel generate --resume <JOB_ID>
```

Re-reads `project.json`. If claims exist, runs QA. If a story exists, compiles into the same job tree. Does not regenerate images or audio unless the agent runs those tools again.

`--force` compiles even when monetization is not ready (still do not GenerateImage unless `ready_to_publish`).

Completed expensive assets are not overwritten by a second `generate` unless compile inputs changed and the agent re-runs compile.

## What the agent still does

Cursor Grok is the researcher, story writer, and GenerateImage operator. Code does title parse, factcheck, originality, compile, YouTube pack, Kokoro, FFmpeg. Do not invent a second workflow.
