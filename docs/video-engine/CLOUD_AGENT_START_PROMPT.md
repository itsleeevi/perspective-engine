Read AGENTS.md, docs/video-engine/QUALITY_BAR.md, and all applicable Cursor project rules.

This repository contains a complete multi-channel video-generation engine.

Do not invent a new production workflow.

Use the repository's canonical generation pipeline and permanent channel configuration.

Copy the GRAMMAR in docs/video-engine/QUALITY_BAR.md (kid map, recognizable cartoon locks, oversized focal object, unique cinema stills, punchy Short). Never copy the spines of the reference cuts.

Generate:

Channel: <CHANNEL>
Title: <TITLE>

Run:

```text
.venv/bin/python -m channel generate --channel <mode> --title "<TITLE>"
```

Or, when the operator already has timestamped stills (`[00-00]_….jpg`) and narration audio:

```text
.venv/bin/python -m channel drop --channel <mode> --title "<TITLE>"
```

Print the `drop/` folder. After files land, `.venv/bin/python -m channel assemble <JOB_ID>` writes a 4K MP4 without burned captions.

Then fill research, story, and narration in `artifacts/<JOB_ID>/project.json` using the **master prompt** (`MASTER`) in the prompt module named in the manifest. Same staged loop on every channel; DNA customized per mode. Resume with `--resume <JOB_ID>`. Stop at `WAIT_AUDIO`. Print the `script.txt` path. Do not write scenes before the operator returns with audio. After timestamps, deliver Google Flow prompts in batches of 20 and wait for **Reply "next"**. Do not emit `flow_prompts` until originality_score ≥ 80 and ready_to_publish.

Do not alter permanent channel configuration during a normal generation job.

Use a unique job ID.

When complete (or when blocked on the operator), report:

- job ID
- state (`WAIT_AUDIO` / `WAIT_DROP` / `WAIT_IMAGES` / `READY`)
- `script.txt` path
- `OPERATOR.md` path
- final video path if assembled
- thumbnail path
- Short path if generated
- metadata path
- QA scores
- any warnings

Internal modes: `what_they_really_think`, `behind_the_business` (How They Really Make Money), `how_they_took_over`.
