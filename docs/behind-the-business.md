# How They Really Make Money — production system

This is the playbook for the YouTube channel **How They Really Make Money** (`@HowTheyReallyMakeMoney`). Internal mode stays `behind_the_business`. It reuses the shared `channel/` video engine (research tools, stills, Kokoro, assemble, originality, Shorts, YouTube pack). It is **not** What They Really Think with different titles.

Read this fully before starting a business cut. After a cut ships, update `docs/business/<slug>.md` and `docs/business/README.md`.

What They Really Think stays on `docs/custom-videos.md`. How They Took Over stays on `docs/how-they-took-over.md`. Do not mix the three story grammars.

## Channel mode

```text
CHANNEL_MODE = behind_the_business
```

Always pass it. Do not detect the channel from the title alone.

```text
.venv/bin/python -m channel generate --channel behind_the_business --title "How Costco Really Makes Money"
.venv/bin/python -m channel init --channel behind_the_business "How Costco Really Makes Money"
```

Cloud / parallel runs must use `generate` (writes `artifacts/<JOB_ID>/`). `init` is sequential local only.

The same engine still starts a history cut the old way:

```text
.venv/bin/python -m channel init "What Einstein Really Thought About God"
```

Config lives in `channel/config.py` as `BEHIND_THE_BUSINESS` / `config_for("behind_the_business")`. Stage prompts live in `channel/business_prompts.py`. Title parsing lives in `channel/business_title.py`.

## Core promise

Explain the hidden systems, economics, decisions, incentives, and business models behind companies people already know.

The viewer should finish thinking: I use this company all the time and had no idea THAT was how the business actually worked.

## Sacred rules

These are non-negotiable on every Behind The Business title (and the same bar applies on What They Really Think):

1. **Fresh research for every video.**
2. **Different story architecture** for each company.
3. **Original narration, not rewritten articles or YouTube transcripts.**
4. **Unique scenes and diagrams** built around that company's actual business.
5. **unique story engine** — one object / place / reversal that would not work on any other cut.

If you could swap the company names and keep the same video, throw it out. Other YouTube videos are competitive research, not sources or scripts.

## The business mystery

Do **not** structure episodes as company history → founder → products → revenue → conclusion.

Find one central surprising question. Research verifies the answer. The title analyzer must **not** assume the hidden engine (membership, real estate, take-rate, etc.).

## Length and voice

- Target about **22 minutes** (1200–1500 seconds). Prefer 15 excellent minutes to 25 padded minutes.
- Kokoro speed **1.0–1.15** (default **1.15**; never below **1.0** on a new title). Same Liam pacing as What They Really Think.
- Script **4400–5500 words** (ideal 4600–5200) so a 1.15 cut still lands ~20–25 minutes.
- Stills still change every **4–8 seconds**.
- Voice: a smart friend explaining why a company works so a five-year-old can follow while watching. One idea at a time. Short spoken sentences. **Do not read long numbers** aloud — round to a sayable figure. Exact digits stay in claims. Not an MBA lecture, not financial TV, not TikTok hype.

## Research

Before writing: filings first (annual reports, SEC/equivalent, investor decks, earnings calls), then reputable financial journalism. Wikipedia is a seed only. Other YouTube videos are competitive research, not sources.

Never invent revenue, profit, margin, subscribers, share, valuation, costs, or prices. Store `fiscal_period`, `source_date`, and `data_date`. Derived numbers store `calculation` and `inputs`. If unit economics are not public, say so.

No investment advice. Use "investors valued…" not "you should buy…".

## Story movement (guidance, not a stamp)

Mystery → what people think it is → first surprise → how the machine works → why it is powerful → the strange decision that makes sense → the money → the moat → the weakness → the real business.

Vary hooks. Do not open every episode with "This company isn't really X. It's actually Y."

Retention: something new every 20–40 seconds; a major insight every 60–120 seconds; a real shift around 5 / 10 / 15 / 20 minutes. `channel/business_qa.py` checks 60-second segments and dead sections.

## Visuals

`BEHIND_THE_BUSINESS_VISUAL_STYLE` is frozen in `channel/config.py`: clean modern flat 2D, high contrast, diagrams and money flows. Not the muted historical What They Really Think palette. Not photoreal. Not 3D corporate.

Rotate scene types (store, money flow, chart, map, customer, flashback). One chart = one idea. `$100` breakdowns only when the filings support them.

Company names stay out of image prompts. Do not recreate ads shot-for-shot.

## Shorts, thumbs, metadata

- One Short per long video: **30–55 seconds**, one mechanism, not a 22-minute compress.
- Thumbnail: one company symbol + one business idea, **2–5 words**, no lying.
- YouTube copy uses the How They Really Make Money attribution and an educational + synthetic-media disclosure.
- Channel handle: **@HowTheyReallyMakeMoney**. Profile **800×800** JPEG and cover **2560×1440** JPEG (`python -m channel branding --channel behind_the_business --profile … --cover …`). Paste `assets/youtube/behind_the_business_about.txt` into the channel About box. Cover art must keep the story in the center 1546×423 safe band (do not upload the safe-zone preview).
- After assemble: `python -m channel youtube <slug>`.
- Originality compares against `docs/business/README.md` (last 10 business videos), not against Freud or Einstein.

## Pipeline

```text
 1. Read this file + docs/business/README.md (do not copy a shipped mystery).

 2. .venv/bin/python -m channel init --channel behind_the_business "<title>"
    Optional: --instructions "..." --duration 1320 --skip-seed
    Writes channel/projects/<slug>/project.json with channel_mode set.

 3. RESEARCHER using channel/business_prompts.py. Fill research.claims from
    filings first. Fill project.business (model, moats, risks, dated metrics).
    Never invent numbers. Do not assume the hidden engine.

 4. .venv/bin/python -m channel qa <slug>
    Fix rejected financial claims. Do not write narration until factcheck is honest.

    5. STORY + NARRATION (4400–5500 words, mystery spine, title_payoff in the VO).
    BIBLES: company visual_identity; names stay out of image prompts.

 6. .venv/bin/python -m channel chunks <slug>
    One Scene per line. Rotate BUSINESS_VISUAL_TYPES.

 7. .venv/bin/python -m channel qa <slug>
    Need originality_score ≥ 80 vs docs/business/ and ready_to_publish
    (includes financial_accuracy and business_analysis_depth).

 8. .venv/bin/python -m channel compile <slug>
    Then scripts/lint_story.py and scripts/lint_originality.py.

 9. GenerateImage jobs only after those gates pass. Then
    scripts/run_short.py and scripts/run_custom_video.py.

10. python -m channel youtube <slug>
    Update docs/business/<slug>.md + README.md.
```

Score or explore titles first:

```text
.venv/bin/python -m channel score-title "How Visa Really Makes Money"
.venv/bin/python -m channel suggest-titles Costco
```
