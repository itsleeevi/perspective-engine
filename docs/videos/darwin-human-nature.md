# What Darwin Really Thought About Human Nature

Channel-engine cut (`python -m channel init`). Do not clone this spine for a different title.

Facts in the narration run through **August 2026** (Notebook B still public in Cambridge). Do not write “today is [date]” into the VO.

## Spine

Third-person documentary. `the_thought`: **He thought people are animals who learned to be kind.** A five-year-old can retell it: Darwin drew a fork with “I think” on top; a boy bought for a button showed him we are one kind; Origin almost left us out; Descent said mind differs in degree not kind and conscience grew from the pack; later men stole “survival of the fittest” to say let the weak die. Silent cards: **I Think** → **Jemmy Button** → **Light Thrown** → **Moral Sense** → **False Fitness**.

Speak the names: **HMS Beagle**, **On the Origin of Species**, **The Descent of Man**, **Jemmy Button**, **Orundellico**, **Tierra del Fuego**, **Robert FitzRoy**, **Alfred Russel Wallace**, **Herbert Spencer**. Keep those names out of image prompts.

Signature prop: **THE_FORK** in exactly 6 long scenes — a huge pale Y-shaped birch twig, thick as a wrist, bright cream on a dark table, never a faint notebook doodle.

The opinion is the 1837 fork, the pearl button, the Origin tease, the conscience chapter, and the stolen slogan — not a diary line that says “human nature is X.”

## Do not copy onto the next title

- “He thought people are animals who learned to be kind”
- “Two words in a notebook: I think”
- “If every living thing sits on one fork, where do we sit?”
- Notebook B / page 36 / pale Y-twig as the only returning object
- Jemmy Button bought for a pearl button as the only Beagle beat
- “Light will be thrown on the origin of man and his history” as the only Origin tease
- Degree not kind / moral sense from the pack as this title’s closer
- False Fitness / Social Darwinism as the stolen-slogan chapter
- Elon MIT demon / THE_CIRCLE / Grok parents
- Bezos tortoise / hare / Gradatim
- Altman inbox / essay / the check
- Jobs Mac / Xerox / no taste
- Einstein telegram / letter / Spinoza

## Technical

| | |
|---|---|
| Project | `channel/projects/darwin-human-nature/project.json` (`_build.py`) |
| Fixture | `fixtures/darwin-human-nature.json` |
| Stills | `fixtures/darwin-human-nature_stills.py`, jobs `fixtures/darwin-human-nature_v1_image_jobs.json` |
| Spec | `fixtures/video_specs/darwin-human-nature.json` (`still_prefix` **v1**) |
| Voice | Kokoro `am_liam`, speed 1.15, sentence pause **0.06**, clause **0.02**, scene hold **0.28**, burned-in captions |
| Output | `assets/output/what_darwin_really_thought_about_human_n_final.mp4` (3840×2160, **7:33**, ~187 MB) |
| Sync | cut error 16.67 ms |
| Short | `assets/output/darwin-human-nature_short.mp4` (1080×1920, **25.4s**, 7 shots, cut error 15.67 ms, branded end card) |
| Thumb | `assets/youtube/darwin_human_nature_thumbnail_1280x720.jpg` (overlay **I THINK**) |
| Shorts thumb | `assets/youtube/darwin_human_nature_short_thumbnail_1080x1920.jpg` (overlay **I THINK**) |
| Description | `assets/youtube/darwin_human_nature_description.txt` (honest synthetic-media disclosure) |
| Shorts description | `assets/youtube/darwin_human_nature_short_description.txt` — `Watch the full video:` / URL / punch paragraph |
| Tags | `assets/youtube/darwin_human_nature_tags.txt` |
| Thumb job | `fixtures/darwin-human-nature_thumbnail_image_jobs.json` |
| Shorts thumb job | `fixtures/darwin-human-nature_short_thumbnail_image_jobs.json` |

Chapters: Intro → I Think (0:32) → Jemmy Button (2:04) → Light Thrown (3:36) → Moral Sense (4:52) → False Fitness (6:10).

Thumbnail stills use the same recognizable cartoon face as the public figure (balding dome, long grey-white beard, black coat), not a photograph.

## Playbook

`docs/custom-videos.md`
