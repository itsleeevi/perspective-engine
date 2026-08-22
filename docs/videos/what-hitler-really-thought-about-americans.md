# What Hitler Really Thought About Americans

Last assembled: v3 (numbered-fakes cut), **3:50**, 4K, 62 shots. Do not clone this spine for a different title.

## Spine (v3)

Third-person narrator. Cold open: they expected maps, they found a cowboy novel. **Five fakes**, counted out loud: (1) the German western paperback, (2) Hollywood / zoo glass, (3) Detroit brochure, (4) radio flyer, (5) the Atlantic as a moat. Then the crack (1936), December, he declares war like cancelling a subscription, GIs climb onto the stage, same drawer / same book. Button: he fell in love with a fake America and attacked the real one.

This replaced v1 (first-person clone of the Putin roast) and v2 (same paperback idea, too literary, too many random inserts, Kokoro raced ~250 wpm so cuts felt unsynced).

## Do not copy onto the next title

- The five-fakes list, the cowboy paperback as the engine, zoo glass, subscription-cancel war
- Putin’s plane-clap / coupon / two Americas / attention machine / familiarity button

## Technical

| | |
|---|---|
| Fixture | `fixtures/hitler_americans.json` |
| Stills | `fixtures/hitler_americans_stills.py`, jobs `fixtures/hitler_v3_image_jobs.json` |
| Prefix / dir | `hitler_v3_` → `assets/grok_hitler_v3/` |
| Runner | `scripts/run_hitler_americans.py` (`NARRATION_WPM=205`, thread `hitler-americans-v3`) |
| Voice | Kokoro `am_liam`, speed 1.0, 80-word packs (`adapters/voice/kokoro.py`) |
| Output | `assets/output/what_hitler_really_thought_about_america_final.mp4` (3840×2160, **3:50**, ~132 MB) |
| Sync | cut error ≤ 16 ms (half a 30 fps frame); `NARRATION_WPM=205` matches Kokoro speed 1.0 |
| Thumb | `assets/youtube/thumbnail_upload_1280x720.jpg` (16:9 JPEG; do not upload the 3:2 PNG) |
| Description | `assets/youtube/hitler_americans_description.txt` |

Stills: no Nazi symbols; hero is clean-shaven charcoal-suit official (mustache generations get blocked). Lock THE BOOK and THE OFFICE across frames.

## Playbook

`docs/custom-videos.md`
