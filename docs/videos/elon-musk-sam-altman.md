# What Elon Musk Really Thinks About Sam Altman

Channel-engine cut (`python -m channel generate --channel what_they_really_think`). Do not clone this spine for a different title.

Facts in the narration run through **August 2026** (Oakland advisory jury May 18, 2026). Do not write “today is [date]” into the VO.

## Spine

Third-person documentary. `the_thought`: **He wanted the chair. Sam kept it.** A five-year-old can retell it: two friends put a long table in a lab; Elon wanted the tall wooden seat; the 2017 Honest Thoughts mail said no; he called it the final straw and left; Sam sat down; ChatGPT got famous without him; he built a table next door; he sued; the jury said he waited too long. Silent cards: **Honest Thoughts** → **Final Straw** → **Talking Box** → **Five Days** → **Next Door** → **Too Late**.

Speak the names: **OpenAI**, **ChatGPT**, **xAI**, **Grok**, **Tesla**, **Microsoft**, **GPT-4**. Keep those names out of image prompts.

Signature prop: **THE_EMPTY_CHAIR** in exactly 6 long scenes — a huge empty pale wooden chair at the head of a long table, oversized, high contrast, never a tiny stool.

Cartoon impersonation of both men via `visual_lock` (flat 2D, not photoreal, not cloned voices). That is a recognizable cartoon of the real person. Elon lock: rectangular face, strong broad jaw, tousled dark hair, receding temples, light stubble, plain black crew-neck t-shirt. Sam lock: oval face, large light eyes, messy wavy-curly brown hair, tan camel crew-neck sweater. Do not make them twins. Reuse `channel/character_locks.json`. Hashed photo + sheet: `channel/character_sheets/4a7d89fd.png` + `d44eae5a.png` (black shirt); `be1e2416.png` + `2f577b1a.png` (tan sweater).

## Do not copy onto the next title

- “He wanted the chair. Sam kept it.”
- Honest Thoughts / final straw / empty wooden boss seat as the only engine
- “Talking Box” / ChatGPT-after-he-left as the only reversal
- Five Days / board wobble as the only 2023 beat
- Next-door table / 97.4 billion dare / “swindler” as the only later beat
- Too Late / kitchen-timer statute as the only closer
- Elon MIT demon / THE_CIRCLE / Grok parents / “They ruled on a calendar, not the story”
- Bezos tortoise / hare / Gradatim
- Altman inbox / essay / the check
- Trump blank gold nameplate / fee vs guess
- Jobs Xerox / no taste / “take the man's chair”
- Freud “The chair is empty. The hour is not over.”

## Technical

| | |
|---|---|
| Project | `channel/projects/elon-musk-sam-altman/project.json` |
| Fixture | `fixtures/elon-musk-sam-altman.json` |
| Stills | `fixtures/elon-musk-sam-altman_stills.py`, jobs `fixtures/elon-musk-sam-altman_v1_image_jobs.json` (207 long) |
| Spec | `fixtures/video_specs/elon-musk-sam-altman.json` (`still_prefix` **v1**, `image_token` **4d0b8f80**, chunk 4–8s / target 6.5) |
| Voice | Kokoro `am_liam`, speed 1.15, sentence pause **0.06**, clause **0.02**, scene hold **0.28**, burned-in captions |
| Output | `assets/output/what_elon_musk_really_thinks_about_sam_a_final.mp4` (3840×2160, **21:40**, ~548 MB) |
| Sync | cut error 16.67 ms |
| Short | `assets/output/elon-musk-sam-altman_short.mp4` (1080×1920, **28.6s**, 6 shots, cut error 15.67 ms, branded end card) |
| Thumb | `assets/youtube/elon_musk_sam_altman_thumbnail_1280x720.jpg` (overlay **THE CHAIR**) |
| Shorts thumb | `assets/youtube/elon_musk_sam_altman_short_thumbnail_1080x1920.jpg` (overlay **THE CHAIR**) |
| Description | `assets/youtube/elon_musk_sam_altman_description.txt` (honest synthetic-media disclosure) |
| Shorts description | `assets/youtube/elon_musk_sam_altman_short_description.txt` — `Watch the full video:` / URL / punch paragraph / disclosure |
| Tags | `assets/youtube/elon_musk_sam_altman_tags.txt` |
| Thumb job | `fixtures/elon-musk-sam-altman_thumbnail_image_jobs.json` |
| Shorts thumb job | `fixtures/elon-musk-sam-altman_short_thumbnail_image_jobs.json` |
| Originality | 89.3, `ready_to_publish` |

Chapters: Intro → Honest Thoughts (1:21) → Final Straw (4:52) → Talking Box (9:01) → Five Days (12:11) → Next Door (15:11) → Too Late (18:18).

Thumbnail stills use the same recognizable cartoon face as the public figure (rectangular jaw, tousled dark hair, black t-shirt) plus the huge empty pale wooden chair, not a photograph. GenerateImage passes the hashed photo then the cartoon sheet from `channel/character_sheets/`.

## Playbook

`docs/custom-videos.md` — new long cuts are **20–25 minutes** (4400–5500 words).
