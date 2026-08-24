# How Airbnb Makes Billions Without Owning Hotels

How They Really Make Money cut (`python -m channel generate --channel behind_the_business`). Compiled and QA-ready; long assemble is not on this branch. Do not clone this mystery for a different company.

## Spine

Customer mystery, not a 2008 living-room biography. `the_thought`: **They sell the night, not the building.** Cold open: a brass host key on a paper night slip, not a hotel drawer. Silent cards: **Host Key** → **Agent Line** → **Night Slip** → **Split Fee** → **Cheap Growth** → **Empty Hotel** → **Cash First** → **Open Key**.

The FY2025 10-K files the company as an agent. It does not control the properties, fulfill the rental, bear inventory risk, or set prices. Revenue is 12.241 billion dollars on 91.273 billion of gross booking value (about 13.4 percent blended take; Q4 implied take 13.6 percent). Nights and seats booked: 533.0 million. Net income 2.5 billion. Operating cash flow 4.6 billion. Cost of revenue 2.086 billion. Hosts: over 5 million. Signature prop: brass host key on a night slip. Related tease: a cart that looks like a store while a computer meter pays the year.

## Do not copy onto the next title

- “They sell the night, not the building”
- Brass host key on a night slip as the returning object
- Empty hotel / missing deed as the decoy lobby
- Agent vs principal / GBV 91.273 vs revenue 12.241 as the only surprise
- Split guest+host fee migrating to a 15.5 percent host-side list
- Check-in as the revenue bell / unearned fees as the waiting room
- Opening on a key-that-never-hung-in-a-hotel-drawer beat
- Ending on “ask who sold the night, not who poured the foundation”
- Thumbnail text **NOT THE BUILDING**
- Visa's four desks, Costco's door card, Amazon's cream cart, or a founded-in-X stamp

## Technical

| | |
|---|---|
| Job | `artifacts/airbnb-makes-billions-without-owning-hotels__20260824_040627__3b23b2/` |
| Project | job `project.json` |
| Fixture | job `fixtures/airbnb-makes-billions-without-owning-hotels.json` |
| Stills | job `fixtures/airbnb-makes-billions-without-owning-hotels_stills.py`, jobs `airbnb-makes-billions-without-owning-hotels_v1_image_jobs.json` (222 long) |
| Spec | job `fixtures/video_specs/airbnb-makes-billions-without-owning-hotels.json` |
| Voice | Kokoro `am_liam`, speed 1.15, one utterance per scene + 0.28s hold, burned-in captions |
| Script | 4446 words, 222 long scenes, 18 sources, `originality_score` 100 / `ready_to_publish` |
| Output | not assembled on this commit |
| Thumb | overlay **NOT THE BUILDING** (job not rendered) |
| Thumb job | job `fixtures/airbnb-makes-billions-without-owning-hotels_thumbnail_image_jobs.json` |

Signature prop: `THE_HOST_KEY` in 6 long scenes. Company name stays out of image prompts. GenerateImage filenames use hashed tokens, then copy onto assemble names.

## YouTube pack

Refresh with `python -m channel youtube airbnb-makes-billions-without-owning-hotels__20260824_040627__3b23b2` after assemble. Upload the JPEG, not the 3:2 PNG. After the long video is live, set `youtube.full_video_url` and re-run. Tick YouTube Studio's altered/synthetic content checkbox.

**Title:** How Airbnb Makes Billions Without Owning Hotels

**Short title:** The Key That Is Not a Hotel

**Thumbnail text:** NOT THE BUILDING

**Description** (search phrase in the first 200 characters):

```
How Airbnb makes billions without owning hotels: they sell the night, not the building.

The FY2025 10-K files the company as an agent. Revenue was 12.241 billion dollars on 91.273 billion of gross booking value. Nights and seats booked were 533.0 million. The company does not control the properties, set prices, or bear inventory risk.

Sources / further reading:
- Airbnb, Inc. Form 10-K for the fiscal year ended December 31, 2025
- Airbnb Q4 and Full Year 2025 results and shareholder letter
- Airbnb Q4 2025 earnings call (February 12, 2026)

Educational analysis of a business model. Not investment advice.
```

## Playbook

`docs/behind-the-business.md`
