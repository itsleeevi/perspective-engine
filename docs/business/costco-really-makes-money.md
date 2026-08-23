# How Costco Really Makes Money

Second How They Really Make Money cut (`python -m channel init --channel behind_the_business`). Do not clone this mystery for a different company, and do not clone Visa's four-desk hop onto it.

## Spine

Customer mystery, not company history. `the_thought`: **The card at the door is the real checkout.** Cold open: the exit receipt is long and loud; that noisy till is not how the year got paid. Silent cards: **Exit Receipt** → **Thin Stickers** → **Door Money** → **Gold Upgrade** → **Why Copycats Fail** → **Pay For The Door**.

Merchandise in fiscal 2025 ran a thin 11.12 percent gross margin on $269.912 billion of net sales. Membership fees were $5.323 billion next to $10.383 billion of operating income — about half if you line the two numbers up, not a fully allocated P&L. Executive members were under half the paid base and about 73.6 percent of sales. Signature prop: the gold card at the door. Related tease: Sam's Club.

## Do not copy onto the next title

- “The card at the door is the real checkout”
- The long exit receipt as the decoy till
- A blank gold membership card as the returning object
- Thin sticker / 11.12 percent merchandise gross margin as the only surprise
- “You bought the year at the door”
- Executive members as “under half the base, most of the sales”
- Opening on a receipt-then-look-back-at-the-door beat
- Ending on Sam's Club / “hoping the receipt will do that job”
- Thumbnail text **PAY AT THE DOOR**
- Visa's four desks, authorization pulse, fat line vs thin pipe, or “plastic is a costume”

## Technical

| | |
|---|---|
| Project | `channel/projects/costco-really-makes-money/project.json` |
| Fixture | `fixtures/costco-really-makes-money.json` |
| Stills | `fixtures/costco-really-makes-money_stills.py`, jobs `fixtures/costco-really-makes-money_v1_image_jobs.json` (226 long) |
| Spec | `fixtures/video_specs/costco-really-makes-money.json` |
| Voice | Kokoro `am_liam`, speed 0.92, one utterance per scene + 0.28s hold, burned-in captions |
| Output | `assets/output/how_costco_really_makes_money_final.mp4` (3840×2160, **20:30**) |
| Sync | cut error 16.67 ms (half a 30 fps frame) |
| Short | `assets/output/costco-really-makes-money_short.mp4` (1080×1920, **35.5s**, 7 shots, cut error 14.33 ms) |
| Thumb | `assets/youtube/costco_really_makes_money_thumbnail_1280x720.jpg` (1280×720, overlay **PAY AT THE DOOR**) |
| Description | `assets/youtube/costco_really_makes_money_description.txt` (honest synthetic-media disclosure; not investment advice) |
| Short description | `assets/youtube/costco_really_makes_money_short_description.txt` |
| Tags | `assets/youtube/costco_really_makes_money_tags.txt` |
| Thumb job | `fixtures/costco-really-makes-money_thumbnail_image_jobs.json` |
| Shorts thumb job | `fixtures/costco-really-makes-money_short_thumbnail_image_jobs.json` |

Signature prop: THE_GOLD_CARD in 6 long scenes. Company name stays out of image prompts.

## YouTube pack

Refresh with `python -m channel youtube costco-really-makes-money` (assemble JSON stamps chapter times). Upload the JPEG, not the 3:2 PNG. After the long video is live, set `youtube.full_video_url` and re-run. Tick YouTube Studio's altered/synthetic content checkbox.

**Title:** How Costco Really Makes Money

**Short title:** Why You Pay Before You Shop

**Thumbnail text:** PAY AT THE DOOR

**Description** (search phrase in the first 200 characters):

```
How Costco really makes money: the card at the door is the real checkout, not the long receipt at the exit.

You pay for the year before you pay for the food. Fiscal 2025 filings show $5.323 billion of membership fees next to $10.383 billion of operating income, while merchandise gross margin was only 11.12 percent of net sales. Executive members were under half the paid base and about 73.6 percent of sales.

Sources / further reading:
- Costco Wholesale Corporation Form 10-K for the fiscal year ended August 31, 2025
- Costco Wholesale Corporation Reports Fourth Quarter and Fiscal Year 2025 Operating Results (September 25, 2025)
- Costco Wholesale Corporation Form 10-Q for the quarter ended May 10, 2026
- Costco Wholesale Corporation Reports Third Quarter Fiscal 2026 Results (May 28, 2026)

Educational analysis of a business model. Not investment advice.

0:00 Intro
0:25 Exit Receipt
2:56 Thin Stickers
6:34 Door Money
10:17 Gold Upgrade
13:18 Why Copycats Fail
17:32 Pay For The Door

Researched and written for How They Really Make Money from company filings and primary sources.

Illustrated documentary. Stills and narration are generated. Research and story are original to this channel. Educational business analysis, not investment advice. Not a photograph of any real person.
```

**Tags:** costco, how they really make money, how costco makes money, warehouse club, membership fees, business documentary, how the company makes money, illustrated documentary, the gold card, how costco really makes money

## Playbook

`docs/behind-the-business.md`
