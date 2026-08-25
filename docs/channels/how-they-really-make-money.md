# How They Really Make Money

Internal mode: `behind_the_business` (aliases: `how_they_really_make_money`, `htrmm`, `btb`, `business`).
Playbook: `docs/behind-the-business.md`. Config: `BEHIND_THE_BUSINESS`.
Prompts: `channel/business_prompts.py`. Index after ship: `docs/business/`.

Do **not** rename `behind_the_business`. Do **not** apply this grammar to a Think or Takeover title.

## Channel promise

**How does this business really make money?** Viewer finish: I use this company all the time and had no idea THAT was the engine.

## Target audience

People who already use the company and want the hidden economics, not a founder biopic.

## Runtime and narration length

| | Value |
|---|---|
| Runtime | ~20–25 minutes (ideal ~22; 1200–1500s, target 1320) |
| Script | **4400–5500** words (ideal 4600–5200) |
| Spoken pace | 145–155 wpm written; Kokoro **1.15** (never below **1.0** on a new title) |
| Voice | Kokoro `am_liam` (roster may rotate) |
| Costco lock | Kokoro **0.92** — do not recut unless asked |

## Narration personality

Smart friend explaining why a company works. Not MBA, not financial TV, not TikTok hype. Educational analysis, not investment advice.

## Story architecture

```text
mystery → what people think it is → surprise → machine → money → moat → weakness → real engine
```

Not founded-in / founder / product list / revenue today. Analyzer must **not** assume membership, take-rate, real estate, etc. (`unknown until researched`).

## Research priorities

Annual reports, SEC/equivalent filings, investor presentations, earnings calls, shareholder letters, official company information, then credible financial journalism. Wikipedia is a seed only. **Never invent numbers.** Store `fiscal_period` / `source_date` / `data_date`. Derived figures store `calculation` and `inputs`.

Uncover: apparent business, hidden economics, customers, revenue streams, costs, money flow, retention, business model, moat, weakness, real engine.

## Title interpretation

How / Why / The Business Behind… “How Visa Really Makes Money” is this channel. “How Nvidia Took Over AI” is not.

## Scene grammar

Money-flow diagrams, company environments, products — unique to that business. 5–8 chapters. Not WTRT portraits. Not takeover flywheel grammar. One oversized focal object per still; costume-locked extras; no filing-table wallpaper (`docs/video-engine/QUALITY_BAR.md`).

## Visual identity

`BEHIND_THE_BUSINESS_VISUAL_STYLE`: clean modern flat 2D, high contrast, diagrams and money flows. Not muted historical WTRT. Not photoreal. Not 3D corporate.

## Thumbnail strategy

Company symbol + business object. 2–5 words. Default overlay `THE REAL ENGINE`. Empty right third. No on-image text in the still.

## Short strategy

One money-flow surprise, 75–140 words, branded end card, link in description.

## Retention

New every 20–40 seconds; major insight every 60–120 seconds; shift around 5 / 10 / 15 / 20 minutes. `channel/business_qa.py` flags dead sections.

## Originality and monetization

Score vs last 10 in `docs/business/`. Need `financial_accuracy` and `business_analysis_depth`. Do not clone Visa’s desks onto Costco.

## QA thresholds

`originality_score ≥ 80`, `ready_to_publish`, factcheck, business QA ready. No GenerateImage until those pass.
