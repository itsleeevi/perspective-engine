# What Hitler Really Thought About Americans

Last assembled: **v4** (continuous perspective story, silent chapter cards), **5:43**, 4K, 82 shots (77 stills + 5 cards). Do not clone this spine for a different title.

## Spine (v4)

Third-person narrator **inside his mental model**. Cold open: they kicked a door looking for maps, they found a cowboy novel. Silent cards: **The Drawer** → **The Paper West** → **The Glass** → **The Stadium** → **December**. He never went; he built Americans from a German western, movies-as-intel, a Detroit brochure, a radio flyer, an ocean moat. 1936 he hears the crack and puts the book back in the drawer. December the audience climbs onto the stage. Button: he thought they were his. They weren't.

The job of the cut is perspective + teaching: how a man goes to war with a cartoon, not a numbered list of “fakes.”

This replaced v3 (five-fakes lecture, first-person “I will count”, Kokoro at 205 wpm sounding like a newsreader), v2 (too literary, unsynced), and v1 (first-person clone of the Putin roast).

## Do not copy onto the next title

- The five-fakes list, “Stay. I will count,” zoo-glass as a numbered item, subscription-cancel as the only joke
- Putin’s plane-clap / coupon / two Americas / attention machine / familiarity button
- Telegram VO (“Soft cover. German. A boy’s book.”) — write spoken story instead

## Technical

| | |
|---|---|
| Fixture | `fixtures/hitler_americans.json` (`title_style: chapter`, `speak_title_cards: false`) |
| Stills | `fixtures/hitler_americans_stills.py`, jobs `fixtures/hitler_v4_image_jobs.json` |
| Prefix / dir | `hitler_v4_` → `assets/grok_hitler_v4/` |
| Runner | `scripts/run_hitler_americans.py` (`NARRATION_WPM=175`, thread `hitler-americans-v4`) |
| Voice | Kokoro `am_liam`, speed 0.80, ~50-word packs (`adapters/voice/kokoro.py`) |
| Output | `assets/output/what_hitler_really_thought_about_america_final.mp4` (3840×2160, **5:43**, ~195 MB) |
| Sync | cut error ≤ 17 ms (half a 30 fps frame); `NARRATION_WPM=175` matches Kokoro speed 0.80 |
| Thumb | `assets/youtube/thumbnail_upload_1280x720.jpg` (16:9 JPEG; do not upload the 3:2 PNG) |
| Description | `assets/youtube/hitler_americans_description.txt` |

Stills: no Nazi symbols; hero is clean-shaven charcoal-suit official (mustache generations get blocked). Lock THE BOOK and THE OFFICE across frames. Do not put the historical name in image prompts.

## Owed to the next rewrite (v5)

The v4 storyboard predates the system linters and **fails them**: THE BOOK sits in 47/77 frames (budget 6) and THE OFFICE hosts 18 (see `scripts/lint_storyboard.py` on `fixtures/video_specs/hitler_americans.json`). A v5 must fix the prop economy, add `the_thought` (one child-repeatable sentence naming what he believed — say it, show it, say it again; see `docs/custom-videos.md`), keep the (passing) v4 story or better, and render through `scripts/run_custom_video.py` — the per-video runner script is gone.

## Playbook

`docs/custom-videos.md`
