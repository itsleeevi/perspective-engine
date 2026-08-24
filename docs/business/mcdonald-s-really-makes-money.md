# How McDonald's Really Makes Money

Third How They Really Make Money cut (`python -m channel generate --channel behind_the_business`). Do not clone this mystery for a different company, and do not clone Costco's door card or Visa's four-desk hop onto it.

## Spine

Customer mystery, not company history. `the_thought`: **The thicker check is the rent, not the royalty.** Cold open: the tray hits the window; that till noise is not how the Corporation got paid. Silent cards: **The Tray** → **Two Totals** → **The Thicker Envelope** → **Who Keeps The Key** → **The License Without Dirt** → **The Lab Kitchens** → **Why The Invoice Survives** → **Who Signs**.

Systemwide sales are not corporate revenue. Fiscal 2025: $139.4 billion Systemwide next to $26.885 billion consolidated revenues. Inside franchised revenue, rents were $10.442 billion and royalties were $6.018 billion. Conventional operators generally sit on a 20-year key the Company keeps. Developmental licensees pay a royalty and bring their own dirt. Signature prop: the numbered brass store key. Related tease: a rival burger franchise that lets the operator keep more of the site.

## Do not copy onto the next title

- “The thicker check is the rent, not the royalty”
- Two totalling machines / Systemwide versus consolidated as the only surprise
- A numbered brass store key as the returning object
- “The guest paid the restaurant. The operator paid headquarters”
- Developmental license versus conventional key as a name-swap spine
- Thumbnail text **THE RENT CHECK**
- Ending on an unnamed royalty-only rival / “this one ends on the envelope”
- Opening on a drive-thru tray-then-look-at-the-invoice beat
- Costco's exit receipt, gold card, or “pay at the door”
- Visa's four desks, authorization pulse, fat line vs thin pipe, or “plastic is a costume”

## Technical

| | |
|---|---|
| Job | `artifacts/mcdonald-s-really-makes-money__20260823_174817__27d181/` |
| Fixture | `fixtures/mcdonald-s-really-makes-money.json` |
| Stills | `fixtures/mcdonald-s-really-makes-money_stills.py`, jobs `fixtures/mcdonald-s-really-makes-money_v1_image_jobs.json` (233 long) |
| Spec | `fixtures/video_specs/mcdonald-s-really-makes-money.json` |
| Voice | Kokoro `am_liam`, speed 1.15, one utterance per scene + 0.28s hold, burned-in captions |
| Output | `assets/output/how_mcdonald_s_really_makes_money_final.mp4` (3840×2160, **26:03**) |
| Sync | cut error 16.67 ms (half a 30 fps frame) |
| Short | `assets/output/mcdonald-s-really-makes-money_short.mp4` (1080×1920, **31.5s**, 6 shots, cut error 11.33 ms) |
| Thumb | `assets/youtube/mcdonald_s_really_makes_money_thumbnail_1280x720.jpg` (overlay **THE RENT CHECK**) |
| Description | `assets/youtube/mcdonald_s_really_makes_money_description.txt` (honest synthetic-media disclosure; not investment advice) |
| Short description | `assets/youtube/mcdonald_s_really_makes_money_short_description.txt` |
| Tags | `assets/youtube/mcdonald_s_really_makes_money_tags.txt` |
| Thumb job | `fixtures/mcdonald-s-really-makes-money_thumbnail_image_jobs.json` |
| Shorts thumb job | `fixtures/mcdonald-s-really-makes-money_short_thumbnail_image_jobs.json` |

Signature prop: THE_NUMBERED_BRASS_STORE_KEY in 6 long scenes. Company name stays out of image prompts.

## YouTube pack

Refresh with `python -m channel youtube mcdonald-s-really-makes-money` (assemble JSON stamps chapter times). Upload the JPEG, not the 3:2 PNG. After the long video is live, set `youtube.full_video_url` and re-run. Tick YouTube Studio's altered/synthetic content checkbox.

**Title:** How McDonald's Really Makes Money

**Short title:** Why the Rent Beats the Royalty

**Thumbnail text:** THE RENT CHECK

**Description** (search phrase in the first 200 characters):

```
How McDonald's really makes money: the thicker check is the rent, not the royalty. Fiscal 2025 filings show 10.442 billion dollars of franchised rents next to 6.018 billion of royalties, while Systemwide sales were 139.4 billion and consolidated revenues were 26.885 billion.

Sources / further reading:
- McDonald's Corporation Form 10-K for the fiscal year ended December 31, 2025 (filed February 24, 2026)
- McDonald's Corporation Reports Second Quarter 2026 Results (exhibits 99.1 and 99.2)

Educational analysis of a business model. Not investment advice.

0:00 Intro
0:13 The Tray
3:33 Two Totals
7:51 The Thicker Envelope
11:33 Who Keeps The Key
14:46 The License Without Dirt
17:26 The Lab Kitchens
20:31 Why The Invoice Survives
24:11 Who Signs

Researched and written for How They Really Make Money from company filings and primary sources.

Illustrated documentary. Stills and narration are generated. Research and story are original to this channel. Educational business analysis, not investment advice. Not a photograph of any real person.
```

**Tags:** mcdonald's, how they really make money, how mcdonald's makes money, franchise rent, royalty, business documentary, how the company makes money, illustrated documentary, the rent check, how mcdonald's really makes money

## Playbook

`docs/behind-the-business.md`
