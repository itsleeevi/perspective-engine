# What Donald Trump Really Thinks About Elon Musk

Channel-engine cut (`python -m channel generate --channel what_they_really_think`). Do not clone this spine for a different title.

Facts in the narration run through **August 2026** (Wall Street Journal private-talk reporting; Air Force One / Beijing flight reporting). Do not write “today is [date]” into the VO.

## Spine

Third-person documentary. `the_thought`: **He likes Elon as a helper. He talks about selling the car when Elon talks back.** A five-year-old can retell it: Trump parked a shiny red sedan on the lawn when Elon helped; an official said they might sell that same car when Elon argued; the guest badge ran out; they shook hands later, but the car is the honest picture. Silent cards: **Paris Walk** → **Rocketships Nowhere** → **Lawn Lot** → **Guest Days** → **Pork Fight** → **Sell Talk**.

Speak the names: **Donald Trump**, **Elon Musk**, **Tesla**, **SpaceX**, **America PAC**, **DOGE**, **Truth Social**. Keep those names out of image prompts.

Signature prop: **THE_RED_TESLA** in exactly 6 long scenes — a huge cherry-red sedan, oversized like a kid toy car, high contrast, never a tiny version.

Cartoon impersonation of both men via `visual_lock` (flat 2D, not photoreal, not cloned voices). That is a recognizable cartoon of the real person. Trump lock: boxy navy suit, extra-long red necktie, tall swept gold hair mound. Elon lock: rectangular jaw, tousled dark hair, plain black crew-neck t-shirt. Do not make them twins. Reuse `channel/character_locks.json`. Hashed photo + sheet: `channel/character_sheets/73501a76.png` (navy suit); `4a7d89fd.png` + `d44eae5a.png` (black shirt).

## Do not copy onto the next title

- “He likes Elon as a helper. He talks about selling the car when Elon talks back.”
- Red Tesla / White House lawn car lot as the only engine
- Buy-the-car-when-he-helps / sell-the-car-when-he-talks-back as the only reversal
- Guest-clock DOGE badge / 130 days as the only middle beat
- Pork / abomination / terminate the contracts as the only fight beat
- Elon wanted the chair. Sam kept it.
- Bezos tortoise / hare / Gradatim
- Altman inbox / essay / the check
- Jobs Xerox / no taste
- Freud empty chair / the hour is not over
- Trump blank gold hotel nameplate / fee vs guess

## Technical

| | |
|---|---|
| Job | `artifacts/donald-trump-elon-musk__20260826_131432__015022/` |
| Project | `artifacts/donald-trump-elon-musk__20260826_131432__015022/project.json` |
| Fixture | `artifacts/donald-trump-elon-musk__20260826_131432__015022/fixtures/donald-trump-elon-musk.json` |
| Stills | 181 pause stills, jobs in the same job `fixtures/` |
| Spec | `artifacts/donald-trump-elon-musk__20260826_131432__015022/fixtures/video_specs/donald-trump-elon-musk.json` |
| Voice | imported audio (`ingest-audio`), burned-in captions |
| Output | `artifacts/donald-trump-elon-musk__20260826_131432__015022/final/donald-trump-elon-musk.mp4` (3840×2160, **7:49**, ~181 MB) |
| Sync | video 469.27 s / audio 469.25 s (~17 ms) |
| Short | second HITL pass; does not block this long READY |
| Thumb | `assets/youtube/donald_trump_elon_musk_thumbnail_1280x720.jpg` (overlay **THE RED CAR**) |
| Description | `assets/youtube/donald_trump_elon_musk_description.txt` (honest synthetic-media disclosure) |
| Shorts description | `assets/youtube/donald_trump_elon_musk_short_description.txt` — `Watch the full video:` / URL / punch paragraph / disclosure |
| Tags | `assets/youtube/donald_trump_elon_musk_tags.txt` |
| Originality | 100, `ready_to_publish` |

Chapters: Intro → Paris Walk (1:04) → Rocketships Nowhere (1:40) → Lawn Lot (2:34) → Guest Days (3:48) → Pork Fight (4:41) → Sell Talk (6:04).

Thumbnail stills use the same stick-figure doodle construction (navy suit, extra-long red necktie, gold hair mound) plus the huge cherry-red sedan, not a photograph.

## Playbook

`docs/custom-videos.md` — new long cuts are **5–15 minutes** (800–2500 words).
