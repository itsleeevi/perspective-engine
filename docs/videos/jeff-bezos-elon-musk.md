# What Jeff Bezos Really Thinks About Elon Musk

Channel-engine cut (`python -m channel init`). Do not clone this spine for a different title.

Facts in the narration run through **August 2026** (New Glenn pad explosion May 28; VivaTech June; Limp names the BE-4 valve in August). Do not write “today is [date]” into the VO.

## Spine

Third-person documentary. `the_thought`: **He thinks Elon is the hare, and skipping steps does not make you faster.** A five-year-old can retell it: Bezos started Blue Origin first; Musk got to orbit first; Bezos talks about a tortoise, not the name; he lost Pad 39A, sued NASA when SpaceX won the Moon, flew New Glenn, watched a pad blow up, then posted a tortoise after Musk pivoted to a Moon city. Silent cards: **The Picture** → **The Pad** → **The Suit** → **The Rocket** → **The Moon**.

Speak the names: **Amazon**, **Blue Origin**, **SpaceX**, **Tesla**, **NASA**, **New Shepard**, **New Glenn**, **Starship**, **Starlink**, **Project Kuiper**, **Amazon Leo**, **X**. Keep those names out of image prompts.

Signature prop: **THE_TORTOISE** in exactly 6 long scenes — a huge dark-green suitcase-sized tortoise statue with a bright gold shell, dead center, never a pin or stamp.

Bezos almost never names Musk in speeches. The opinion is the crest (Gradatim Ferociter), the protest, the suit, the rocket, the boom, and the captionless animal — not a diary quote that says “I hate him.”

## Do not copy onto the next title

- “He thinks Elon is the hare, and skipping steps does not make you faster”
- “Why does the quieter man talk about an animal instead of naming Elon Musk?”
- Captionless tortoise photo on X as the only cold open
- Gradatim Ferociter / cowboy boots / hatch paint as the only motto beat
- Pad 39A unicorns-in-the-flame-trench as the only 2013 joke
- “You cannot sue your way to the Moon” as this title’s closer
- New Glenn / Jacklyn / May 2026 pad boom as the only rocket chapter
- Elon MIT demon / THE_CIRCLE / Grok parents
- Altman inbox / essay / the check
- Jobs Mac / Xerox / no taste
- Einstein telegram / letter / Spinoza

## Technical

| | |
|---|---|
| Project | `channel/projects/jeff-bezos-elon-musk/project.json` (`_build.py`) |
| Fixture | `fixtures/jeff-bezos-elon-musk.json` |
| Stills | `fixtures/jeff-bezos-elon-musk_stills.py`, jobs `fixtures/jeff-bezos-elon-musk_v1_image_jobs.json` |
| Spec | `fixtures/video_specs/jeff-bezos-elon-musk.json` (`still_prefix` **v1**) |
| Voice | Kokoro `am_liam`, speed 1.15, sentence pause **0.06**, clause **0.02**, scene hold **0.28**, burned-in captions |
| Output | `assets/output/what_jeff_bezos_really_thinks_about_elon_final.mp4` (3840×2160, **8:31**, ~240 MB) |
| Sync | cut error 16.67 ms |
| Short | `assets/output/jeff-bezos-elon-musk_short.mp4` (1080×1920, **25.8s**, 7 shots, cut error 13.33 ms, branded end card) |
| Thumb | `assets/youtube/jeff_bezos_elon_musk_thumbnail_1280x720.jpg` (overlay **THE HARE**) |
| Shorts thumb | `assets/youtube/jeff_bezos_elon_musk_short_thumbnail_1080x1920.jpg` (overlay **THE HARE**) |
| Description | `assets/youtube/jeff_bezos_elon_musk_description.txt` (honest synthetic-media disclosure) |
| Shorts description | `assets/youtube/jeff_bezos_elon_musk_short_description.txt` — `Watch the full video:` / URL / punch paragraph |
| Tags | `assets/youtube/jeff_bezos_elon_musk_tags.txt` |
| Thumb job | `fixtures/jeff-bezos-elon-musk_thumbnail_image_jobs.json` |
| Shorts thumb job | `fixtures/jeff-bezos-elon-musk_short_thumbnail_image_jobs.json` |

Chapters: Intro → The Picture (0:28) → The Pad (2:02) → The Suit (3:32) → The Rocket (5:07) → The Moon (6:45).

Thumbnail stills use the same recognizable cartoon face as the public figure (shaved bald scalp, navy flight jacket, light blue open collar), not a photograph. Musk shots lock to the same cartoon face as the Elon/AI cut (receding swept-back hair, lantern jaw, black t-shirt).

## Playbook

`docs/custom-videos.md`
