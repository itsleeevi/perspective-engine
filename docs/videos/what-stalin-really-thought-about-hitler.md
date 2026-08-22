# What Stalin Really Thought About Hitler

Last assembled: **v4** (Simple History-like flat 2D vector stills, faster Michael, explain-like-five story), **3:31**, 4K, 60 shots (55 stills + 5 cards). Do not clone this spine for a different title.

## Spine (v3/v4 story)

Third-person narrator **inside his mental model**, taught as if the watcher were five. `the_thought`: **He thought if he was nice to a bad man, the bad man would leave him alone.** Cold open says that sentence. Silent cards: **The Toast** → **The Line** → **The Cellar** → **The Phone** → **The Dust**. He drinks to the other man's health because he thinks a paper turned a bad man into a helper. He draws a line like putting a toy away. Birthday wish. Talking in a basement. Lights in the trees he calls a lie. June, a Sunday still dark, the phone. Button: say it like a child one more time. The bad man did not.

v4 changed **pictures and pace**, not the story: educational flat-vector stills (dot eyes, solid colors, red-to-orange portrait gradients) in the Simple History explainer look, Kokoro `am_michael` at **1.05**. Do not replace this with a birth-to-death Wikipedia biography just because the stills look like an explainer channel.

## Do not copy onto the next title

- “He thought if he was nice to a bad man, the bad man would leave him alone”
- “That is a child's deal”, “Say it like a child”, “Be nice. Share. Smile.”
- A Gori-to-funeral lecture (smallpox, seminary, bank robbery, five-year plans, gulags, then Hitler as a footnote)
- The midnight toast as the only cold open, “drank to the other man's health,” “dealer, once paid, stays bought”
- “rented a wolf,” “the toast was a joke,” “hid from the ring of a phone”
- “He thought the other man could be rented”
- “He thought he had put a storm on a leash”
- Hitler-Americans cowboy book / drawer / paper west / zoo-glass / stadium / December
- Putin’s plane-clap / coupon / two Americas / attention machine

## Technical

| | |
|---|---|
| Fixture | `fixtures/stalin_hitler.json` (`the_thought`, `title_style: chapter`, `speak_title_cards: false`) |
| Stills | `fixtures/stalin_hitler_stills.py`, jobs `fixtures/stalin_v4_image_jobs.json` |
| Look | Simple History-like **flat 2D vector**; hero lock `stalin_v4_000.png` |
| Prefix / dir | `stalin_v4_` → `assets/grok_stalin_v4/` |
| Spec | `fixtures/video_specs/stalin_hitler.json` |
| Runner | `scripts/run_custom_video.py` (`NARRATION_WPM=165`, thread `stalin-hitler-v4`) |
| Voice | Kokoro `am_michael`, speed **1.05**, sentence pause 0.16s, clause pause 0.06s |
| Output | `assets/output/what_stalin_really_thought_about_hitler_final.mp4` (3840×2160, **3:31**, ~63 MB) |
| Sync | cut error 16.33 ms (half a 30 fps frame) |
| Short | `assets/output/stalin_hitler_short.mp4` (1080×1920, **31.9s**, cut error 16.0 ms) |
| Thumb | `assets/youtube/stalin_hitler_thumbnail_1280x720.jpg` |
| Description | `assets/youtube/stalin_hitler_description.txt` (long), `stalin_hitler_short_description.txt` (Short) |

Signature prop: THE GLASS (champagne coupe) in 6 scenes. Sets: THE KREMLIN, THE DACHA. No Nazi symbols. Historical names out of image prompts.

## Playbook

`docs/custom-videos.md` — every future title needs `the_thought` (say it, show it, say it again). Look is per title; matching an explainer channel's stills is not permission to copy its Wikipedia narration.
