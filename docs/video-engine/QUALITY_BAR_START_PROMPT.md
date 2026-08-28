# Generate a quality-bar documentary

Paste this into a **new** Cloud or local agent with empty chat history. Replace the channel and title. Do not edit the engine.

```text
Read AGENTS.md, docs/video-engine/CLOUD_AGENT_START_PROMPT.md, and
docs/video-engine/QUALITY_BAR.md. Then read the playbook for the channel:

- What They Really Think → docs/custom-videos.md
- How They Really Make Money → docs/behind-the-business.md
- How They Took Over → docs/how-they-took-over.md

Copy the GRAMMAR of the best-performing uploads. Never copy their spines.

Long-form grammar references (do not clone these plots):
- What Elon Musk Really Thinks About Sam Altman
- How Tesla Took Over the Electric Car Industry
- How Costco Really Makes Money

Short-form grammar references (do not clone these plots):
- How Donald Trump Really Makes His Money
- What Elon Musk Really Thinks About AI
- How Elon Musk Really Makes His Money

Generate:

Channel: <CHANNEL>
Title: <TITLE>

Run:

.venv/bin/python -m channel generate --channel <mode> --title "<TITLE>"

Then fill research, story, bibles, and scenes in artifacts/<JOB_ID>/project.json
using the prompt module named in the manifest.

Quality bar (non-negotiable):
- Fresh research. Unique story engine. Original narration. Unique scenes.
- the_thought: 6–18 words, child-repeatable. Prefer two beats.
- Cold open: one sourced physical contradiction in a specific place.
- Hook says the_thought, then a kid map of 5–8 steps this title owns.
- Chapters ARE those steps. Unique names from this evidence.
- Named public figures: reusable lock in channel/character_locks.json plus
  hashed photo/sheet in channel/character_sheets/. If new, write
  "Same cartoon person every time, do not redesign. Copy this face:" with
  jaw, eyes, hair, ALWAYS-clothes. Three-view hashed sheet. Not twins.
  Expression changes; skull does not. Costume-lock extras.
- Every still: {SET} {who} {physical verb} {one oversized focal object}
  {named lighting}. Accent + empty margin. Unique staging. No wallpaper.
- Signature prop in ≤ 6 scenes, huge / high contrast / same object.
- Person-titled cuts: recognizable cartoon in ~35–42% of stills.
- Company-titled cuts: empty cinematic sets + costume-locked extras OK.
- Short: first sentence ≤ 16 words is the punch. First still is that picture.
  Unique composition every shot. Branded CTA end card.
- originality_score ≥ 80 and ready_to_publish before flow_prompts.
- Do not modify the video engine, channel prompts, or QA thresholds.

Resume with --resume <JOB_ID>. Use a unique job ID.

When complete, report job ID, final / thumb / Short paths, QA scores, and
whether the cut would still look researched if the tools were hidden.
```

Internal modes: `what_they_really_think`, `behind_the_business` (How They Really Make Money), `how_they_took_over`.
