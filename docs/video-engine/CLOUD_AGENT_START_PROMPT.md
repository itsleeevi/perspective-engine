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

Then fill research, story, bibles, and scenes in `artifacts/<JOB_ID>/project.json` using the prompt module named in the manifest. Resume with `--resume <JOB_ID>`. Run all research, validation, originality, retention, visual, monetization, rendering, and final QA stages required by the repository.

Do not alter permanent channel configuration during a normal generation job.

Use a unique job ID.

When complete, report:

- job ID
- final video path
- thumbnail path
- Short path if generated
- metadata path
- QA scores
- any warnings

Internal modes: `what_they_really_think`, `behind_the_business` (How They Really Make Money), `how_they_took_over`.
