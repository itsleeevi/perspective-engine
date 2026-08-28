# What Freud Really Thought About Women

Channel-engine cut (`python -m channel init`). Do not clone this spine for a different title.

Facts in the narration run through **August 2026** (Berggasse 19 is a museum; a 2025 *History of Psychology* paper re-reads the Bonaparte/Jones riddle). Do not write “today is [date]” into the VO.

This is a **20–25 minute** title (4412 words). Do not shrink it back to 8 minutes.

## Spine

Third-person documentary. `the_thought`: **He thought a woman was a man who had lost something.** A five-year-old can retell it: a girl walked out of the hour and he kept the folder; he drew girls as little men who had lost a piece; a colleague said the first picture was backwards and he kept it; he called adult women a dark continent and still gave the hall a map; a daughter stayed; the famous “what does a woman want” line is secondhand and does not cancel the papers. Silent cards: **Walkout** → **Little Men** → **Horney's No** → **Dark Continent** → **Anna Stays** → **Unanswered**.

Speak the names: **Sigmund Freud**, **Ida Bauer**, **Dora**, **Berggasse 19**, **Fragment of an Analysis of a Case of Hysteria**, **Three Essays on the Theory of Sexuality**, **Karen Horney**, **The Flight from Womanhood**, **Helene Deutsch**, **The Question of Lay Analysis**, **Female Sexuality**, **Lecture 33 Femininity**, **Marie Bonaparte**, **Ernest Jones**, **Anna Freud**, **The Ego and the Mechanisms of Defence**. Keep those names out of image prompts.

Signature prop: **THE_FOLDER** in exactly 6 long scenes — a huge thick cream case folder tied with a bright red ribbon, big as a serving board, high contrast on a dark desk, never a faint paper.

The opinion is the walkout-plus-file, the 1905–1925 little-man ladder, Horney's no, the dark-continent hole next to Lecture 33, and the disputed riddle — not a poster that says he only shrugged.

## Do not copy onto the next title

- “He thought a woman was a man who had lost something”
- “The chair is empty. The hour is not over.”
- Cream case folder / red ribbon as the only returning object
- Dora / Ida Bauer walking out of Berggasse 19 as the only cold open
- Little-man map / two extra jobs / paper doll with a missing pocket as this title’s engine
- Horney's No / first doll / Flight from Womanhood as the only colleague beat
- Dark continent hole cut in a cream map as the only shrug picture
- Anna Stays / night trunk / London child notebooks as the only heir beat
- Was will das Weib / Jones–Bonaparte riddle as the only closer
- Darwin Notebook B fork / Jemmy Button / THE_FORK
- Elon MIT demon / THE_CIRCLE
- Bezos tortoise / hare / Gradatim
- Altman inbox / the check
- Jobs Xerox / no taste
- Einstein telegram / letter / Spinoza

## Technical

| | |
|---|---|
| Project | `channel/projects/freud-women/project.json` (`_build.py`) |
| Fixture | `fixtures/freud-women.json` |
| Stills | `fixtures/freud-women_stills.py`, jobs `fixtures/freud-women_v1_image_jobs.json` (212 long) |
| Spec | `fixtures/video_specs/freud-women.json` (`still_prefix` **v1**, chunk 4–8s / target 6.5) |
| Voice | Kokoro `am_michael` (slug hash), speed 1.15, sentence pause **0.06**, clause **0.02**, scene hold **0.28**, burned-in captions |
| Output | `assets/output/what_freud_really_thought_about_women_final.mp4` (3840×2160, **24:56**, ~671 MB) |
| Sync | cut error 16.33 ms |
| Short | `assets/output/freud-women_short.mp4` (1080×1920, **30.1s**, 6 shots, cut error 16.0 ms, branded end card) |
| Thumb | `assets/youtube/freud_women_thumbnail_1280x720.jpg` (overlay **SHE WALKED OUT**) |
| Shorts thumb | `assets/youtube/freud_women_short_thumbnail_1080x1920.jpg` (overlay **SHE WALKED OUT**) |
| Description | `assets/youtube/freud_women_description.txt` (honest synthetic-media disclosure) |
| Shorts description | `assets/youtube/freud_women_short_description.txt` — `Watch the full video:` / URL / punch paragraph / disclosure |
| Tags | `assets/youtube/freud_women_tags.txt` |
| Thumb job | `fixtures/freud-women_thumbnail_image_jobs.json` |
| Shorts thumb job | `fixtures/freud-women_short_thumbnail_image_jobs.json` |

Chapters: Intro → Walkout (1:02) → Little Men (5:15) → Horney's No (10:00) → Dark Continent (13:51) → Anna Stays (17:38) → Unanswered (20:58).

Thumbnail stills use the same recognizable cartoon face as the public figure (balding dome, neat grey-white beard, round wire glasses, brown three-piece suit), not a photograph. No Nazi flags, no camps, no anatomical diagrams, no photoreal faces.

## Playbook

`docs/custom-videos.md` — new long cuts are **5–15 minutes** (800–2500 words).
