# How Donald Trump Really Makes His Money

How They Really Make Money cut (`python -m channel generate --channel behind_the_business`). Do not clone this mystery for a different person or company. Treat it as a business case study, not a political film.

## Spine

Strange-paper mystery, not a billionaire list and not a campaign. Spoken so a five-year-old can follow: one idea at a time, no long filing digits in the VO. `the_thought`: **The cash is a fee for the name. The big number is a guess about the stuff.** Cold open: he slams a fat magazine guess beside a thin license invoice. Silent cards: **Guess Sheet** → **Father's Keys** → **Tower Debt** → **The Nameplate** → **Studio Check** → **Club Cards** → **The Ticker** → **Four Kinds**. Cartoon tycoon stills (swept gold-blond hair, extra-long red necktie, oversized navy suit) — not a photograph.

Claims keep the exact digits. Spoken VO rounds them. OGE Form 278e (certified June 30, 2026) reports ranges, not one net-worth total. CNBC's August 10, 2026 addition of 2025 foreign real-estate licensing lines is about 59.5 million dollars (up 71 percent from 2024). Developers generally finance and build; the name collects a fee. TMTG FY2025 10-K: about 3.7 million dollars of net sales and about 712 million of net loss, mostly non-cash marks. Schedule 13D/A (December 22, 2025): a trust holds about 42 percent of DJT — ownership, not a paycheck. Forbes March 2026 constructed-balance-sheet estimate: about 6.5 billion dollars, a guess. New York Times 2018: at least about 413 million dollars (then-today's dollars) from Fred Trump's empire. Times 2020: about 197 million from The Apprentice plus about 230 million in related licensing. Signature prop: the blank gold hotel nameplate. Related tease: a branded-hotel developer that pays for a name instead of owning the celebrity.

## Do not copy onto the next title

- “The cash is a fee for the name. The big number is a guess about the stuff”
- A blank gold hotel nameplate as the returning object
- Fat guess binder versus thin license invoice as the only surprise
- Four labels (income / ownership / brand / guess) as a name-swap spine
- Thumbnail text **THE NAME FEE**
- Ending on an unnamed plate-company tease / slamming both papers down again
- Opening on two papers then “which pile is the paycheck”
- Elon's locked pay stub, grant-date costume, or “so who got paid”
- McDonald's rent envelope, numbered key, or “the guest paid the restaurant”
- Costco's exit receipt, gold card, or “pay at the door”
- Visa's four desks, authorization pulse, fat line vs thin pipe, or “plastic is a costume”

## Technical

| | |
|---|---|
| Job | `artifacts/donald-trump-really-makes-his-money__20260824_064906__47231d/` |
| Fixture | `fixtures/donald-trump-really-makes-his-money.json` |
| Stills | `fixtures/donald-trump-really-makes-his-money_stills.py`, jobs `fixtures/donald-trump-really-makes-his-money_v1_image_jobs.json` (254 long) |
| Spec | `fixtures/video_specs/donald-trump-really-makes-his-money.json` |
| Voice | Kokoro `am_liam`, speed **1.15**, one utterance per scene + 0.28s hold, burned-in captions. Spoken VO is child-followable; long filing digits stay in claims. |
| Script | 5113 words, 254 long scenes, 15 sourced claims, `originality_score` 89.5 / `ready_to_publish` |
| Output | `assets/output/how_donald_trump_really_makes_his_money_final.mp4` (3840×2160, **25:45**) |
| Sync | Short cut error 14.67 ms (half a 30 fps frame is 16.67 ms) |
| Short | `assets/output/donald-trump-really-makes-his-money_short.mp4` (1080×1920, **32.8s**, 7 shots, cut error 14.67 ms) |
| Thumb | `assets/youtube/donald_trump_really_makes_his_money_thumbnail_1280x720.jpg` (overlay **THE NAME FEE**) |
| Description | `assets/youtube/donald_trump_really_makes_his_money_description.txt` (honest synthetic-media disclosure; not investment advice; not a campaign film) |
| Short description | `assets/youtube/donald_trump_really_makes_his_money_short_description.txt` |
| Tags | `assets/youtube/donald_trump_really_makes_his_money_tags.txt` |
| Thumb job | `fixtures/donald-trump-really-makes-his-money_thumbnail_image_jobs.json` |
| Shorts thumb job | `fixtures/donald-trump-really-makes-his-money_short_thumbnail_image_jobs.json` |

Signature prop: `THE_BLANK_GOLD_HOTEL_NAMEPLATE` in 6 long scenes. Person and company names stay out of image prompts and GenerateImage filenames (token `2ce0778e`).

## YouTube pack

Refresh with `python -m channel youtube donald-trump-really-makes-his-money` after assemble. Upload the JPEG, not the 3:2 PNG. After the long video is live, set `youtube.full_video_url` and re-run. Tick YouTube Studio's altered/synthetic content checkbox.

**Title:** How Donald Trump Really Makes His Money

**Short title:** The Name Gets the Check

**Thumbnail text:** THE NAME FEE

**Description** (search phrase in the first 200 characters):

```
How Donald Trump really makes his money: the cash is a fee for the name. The big number is a guess about the stuff.

CNBC added about 60 million dollars of 2025 foreign name fees from the ethics disclosure. Forbes's March 2026 estimate is about 6.5 billion dollars. The public ticker sold about 4 million dollars of stuff in 2025.

Educational analysis of a business model. Not investment advice. Not a political campaign film.

Sources / further reading:
- U.S. Office of Government Ethics, certified 2025 annual OGE Form 278e (June 30, 2026)
- CNBC, Trump foreign licensing income surged to $59.5 million (August 10, 2026)
- Trump Media & Technology Group Corp. Form 10-K for the year ended December 31, 2025
- Trump Media & Technology Group Corp. Form 10-Q for the quarter ended June 30, 2026
- Schedule 13D/A Amendment No. 3 (December 22, 2025)
- Forbes, The Definitive Net Worth Of Donald Trump (March 2026 tally)
- New York Times, Trump Engaged in Suspect Tax Schemes as He Reaped Riches From His Father (October 2, 2018)
- New York Times, Tax Records Reveal How Fame Gave Trump a $427 Million Lifeline (September 28, 2020)
```

## Playbook

`docs/behind-the-business.md`
