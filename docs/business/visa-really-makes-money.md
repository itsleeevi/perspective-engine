# How Visa Really Makes Money

First How They Really Make Money cut (`python -m channel init --channel behind_the_business`). Do not clone this mystery for a different company.

## Spine

Customer mystery, not company history. `the_thought`: **Visa gets paid to carry the yes.** Cold open: you tap, you walk out with a cup, Visa did not lend you a dollar. Silent cards: **The Tap** → **Four Desks** → **The Fat Line** → **The Thin Pipe** → **Why Banks Stay** → **The Tiny Cut** → **The Paper Stack** → **Carry The Yes**.

The name on the plastic is a costume. The engine is a four-desk hop (shopper, seller, acquirer, issuer) with Visa in the middle carrying an authorization pulse. The fat line on many merchant statements is interchange moving to the issuer. Visa's published take is the thin remainder after client incentives. Fiscal 2025: $40.0 billion net revenue on $14.2 trillion of payments volume, about 28 cents of Visa net revenue per $100 of payments volume — a blended average, not the fee on a typical U.S. sale. Related tease: Mastercard.

## Do not copy onto the next title

- “Visa gets paid to carry the yes”
- “The coffee is not the product. The yes is.”
- “The plastic is a costume”
- Four desks / four-party hop as the only story engine
- The authorization pulse as the returning object
- Fat line versus thin pipe
- “28 cents of Visa net revenue for every 100 dollars of payments volume”
- “Watch the counter, not the logo”
- Ending on Mastercard / “the colors change. The hop does not”
- Opening on a tap-then-“did not lend you a dollar” cafe beat

## Technical

| | |
|---|---|
| Project | `channel/projects/visa-really-makes-money/project.json` |
| Fixture | `fixtures/visa-really-makes-money.json` |
| Stills | `fixtures/visa-really-makes-money_stills.py`, jobs `fixtures/visa-really-makes-money_v1_image_jobs.json` (216 long) |
| Spec | `fixtures/video_specs/visa-really-makes-money.json` |
| Voice | Kokoro `am_liam`, speed 1.15, one utterance per scene + 0.28s hold, burned-in captions |
| Output | `assets/output/how_visa_really_makes_money_final.mp4` (3840×2160, **16:58**, recut Liam 1.15) |
| Sync | cut error 16.67 ms (half a 30 fps frame) |
| Short | `assets/output/visa-really-makes-money_short.mp4` (1080×1920, **25.2s**, 7 shots, cut error 14.0 ms) |
| Thumb | `assets/youtube/visa_really_makes_money_thumbnail_1280x720.jpg` (1280×720, overlay **EVERY TIME YOU PAY**) |
| Description | `assets/youtube/visa_really_makes_money_description.txt` (honest synthetic-media disclosure; not investment advice) |
| Short description | `assets/youtube/visa_really_makes_money_short_description.txt` |
| Tags | `assets/youtube/visa_really_makes_money_tags.txt` |
| Thumb job | `fixtures/visa-really-makes-money_thumbnail_image_jobs.json` |
| Shorts thumb job | `fixtures/visa-really-makes-money_short_thumbnail_image_jobs.json` |

Signature prop: THE_AUTHORIZATION_PULSE in 6 long scenes. Company name stays out of image prompts.

## YouTube pack

Refresh with `python -m channel youtube visa-really-makes-money` (assemble JSON stamps chapter times). Upload the JPEG, not the 3:2 PNG. After the long video is live, set `youtube.full_video_url` and re-run. Tick YouTube Studio's altered/synthetic content checkbox.

**Title:** How Visa Really Makes Money

**Short title:** What Happens When You Tap Your Card

**Thumbnail text:** EVERY TIME YOU PAY

**Description** (search phrase in the first 200 characters):

```
How Visa really makes money: it gets paid to carry the yes, not to lend the money.

You tap a card every day. Visa usually did not issue it and did not take the credit risk. Fiscal 2025 filings show $40.0 billion of net revenue on $14.2 trillion of payments volume after huge client incentives. The fat line on many merchant statements is interchange moving to the issuing bank.

Sources / further reading:
- Visa Inc. Form 10-K for the fiscal year ended September 30, 2025
- Visa Reports Fiscal Fourth Quarter and Full-Year 2025 Results (October 28, 2025)
- Visa Inc. Annual Report 2025 financial highlights
- Visa Reports Fiscal Third Quarter 2026 Results (July 28, 2026)

Educational analysis of a business model. Not investment advice.

0:00 Intro
0:15 The Tap
1:56 Four Desks
4:08 The Fat Line
6:02 The Thin Pipe
8:12 Why Banks Stay
10:18 The Tiny Cut
13:09 The Paper Stack
15:34 Carry The Yes

Researched and written for How They Really Make Money from company filings and primary sources.

Illustrated documentary. Stills and narration are generated. Research and story are original to this channel. Educational business analysis, not investment advice. Not a photograph of any real person.
```

**Tags:** visa, how they really make money, how visa makes money, payments network, interchange, business documentary, how visa really makes money, illustrated documentary, business model, the authorization pulse

## Playbook

`docs/behind-the-business.md`
