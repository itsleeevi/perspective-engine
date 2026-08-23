# What Elon Musk Really Thinks About AI

Channel-engine cut (`python -m channel init`). Do not clone this spine for a different title.

v2 remake (2026-08-22): simpler spine, spoken company names, no production-clock date in the VO, thick returning circle, Shorts captions in the YouTube safe band. Facts in the narration run through **August 2026** (Grok 4.6 on August 12; SpaceX all-hands on August 14). Do not write “today is [date]” into the VO — that date was only the research cutoff.

## Spine

Third-person documentary. `the_thought`: **He thinks we die unless he builds the machine first.** A five-year-old can retell it: he said AI was a demon you should not summon; he helped start OpenAI; they would not let him run it; he built Grok; he sued and lost on a calendar; he bolted Grok to SpaceX and told the engineers they are the parents. Silent cards: **The Demon** → **The Lab** → **The Suit** → **The Factory** → **The Rocket**.

Speak the names: **OpenAI**, **ChatGPT**, **xAI**, **Grok**, **Tesla**, **SpaceX**, **Colossus**. Keep those names out of image prompts.

Signature prop: **THE_CIRCLE** in exactly 6 long scenes — a huge thick bright white chalk ring on a black floor, large in frame, never a faint stain.

## Do not copy onto the next title

- “He thinks we die unless he builds the machine first”
- “we are summoning the demon”
- “The man who draws a circle and trusts it”
- “He says partly”
- “They will be the parents. It will inherit their thoughts.”
- “AI will become 99 percent of SpaceX's revenue”
- “They ruled on a calendar, not the story”
- Holy water / the circle as the only metaphor
- Colossus / Memphis / 200,000 chips / 122 days as the factory closer
- Altman inbox / essay / the check
- Jobs Mac / Xerox / no taste
- Einstein telegram / letter / Spinoza

## Production rules this remake fixed (keep for the next title)

- Research through the day you write. **Never say today’s calendar date** in the VO (`as of today`, `today is August 22`, `this morning`, `ten days ago`). Date events with months and years. `lint_story.py` rejects production-clock phrasing.
- Speak real org/product names. Do not hide them as “the lab” or “the chatbot shop”.
- Storyline is a blunt simple cartoon a child can retell. Adults still get the dates.
- When the signature prop returns it is the **same obvious object** (high contrast, large), not a faint mark.
- Shorts: punch in the first two seconds. Burned captions sit in the YouTube safe band (above the like / title chrome), never hugging the bottom edge. `graph/captions.py` enforces that.

## Technical

| | |
|---|---|
| Project | `channel/projects/elon-musk-ai/project.json` |
| Fixture | `fixtures/elon-musk-ai.json` |
| Stills | `fixtures/elon-musk-ai_stills.py`, jobs `fixtures/elon-musk-ai_v2_image_jobs.json` |
| Spec | `fixtures/video_specs/elon-musk-ai.json` (`still_prefix` **v2**) |
| Voice | Kokoro `am_liam`, speed 1.15, sentence pause **0.06**, clause **0.02**, scene hold **0.28**, burned-in captions |
| Output | `assets/output/what_elon_musk_really_thinks_about_ai_final.mp4` (3840×2160, **8:14**, ~183 MB) |
| Sync | cut error 16.67 ms |
| Short | `assets/output/elon-musk-ai_short.mp4` (1080×1920, **27.0s**, 7 shots, cut error 14.33 ms, branded end card) |
| Thumb | `assets/youtube/elon_musk_ai_thumbnail_1280x720.jpg` (overlay **THE DEMON**) |
| Shorts thumb | `assets/youtube/elon_musk_ai_short_thumbnail_1080x1920.jpg` (overlay **THE DEMON**) |
| Description | `assets/youtube/elon_musk_ai_description.txt` |
| Tags | `assets/youtube/elon_musk_ai_tags.txt` |
| Thumb job | `fixtures/elon-musk-ai_thumbnail_image_jobs.json` |
| Shorts thumb job | `fixtures/elon-musk-ai_short_thumbnail_image_jobs.json` |

Chapters: Intro → The Demon (0:32) → The Lab (2:04) → The Suit (3:32) → The Factory (5:12) → The Rocket (6:41).

Thumbnail stills use the same recognizable cartoon face as the public figure (receding swept-back hair, lantern jaw, black t-shirt), not a photograph.

## Playbook

`docs/custom-videos.md`
