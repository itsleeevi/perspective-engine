# How They Took Over — production system

This is the playbook for the YouTube channel **How They Took Over** (`@HowTheyTookOver`). Internal mode is `how_they_took_over`. It reuses the shared `channel/` video engine (research tools, stills, Kokoro, assemble, originality, Shorts, YouTube pack). It is **not** What They Really Think and **not** How They Really Make Money with different titles.

Read this fully before starting a takeover cut. After a cut ships, update `docs/takeover/<slug>.md` and `docs/takeover/README.md`.

What They Really Think stays on `docs/custom-videos.md`. How They Really Make Money stays on `docs/behind-the-business.md`. Do not mix the three story grammars.

## Channel mode

```text
CHANNEL_MODE = how_they_took_over
```

Always pass it. Do not detect the channel from the title alone.

```text
.venv/bin/python -m channel generate --channel how_they_took_over --title "How Nvidia Took Over AI"
.venv/bin/python -m channel init --channel how_they_took_over "How Nvidia Took Over AI"
```

Cloud / parallel runs must use `generate` (writes `artifacts/<JOB_ID>/`). `init` is sequential local only.

Aliases: `htto`, `took_over`, `takeover`.

The same engine still starts a history cut and a money-model cut the old way:

```text
.venv/bin/python -m channel init "What Einstein Really Thought About God"
.venv/bin/python -m channel init --channel behind_the_business "How Visa Really Makes Money"
```

Config lives in `channel/config.py` as `HOW_THEY_TOOK_OVER` / `config_for("how_they_took_over")`. Stage prompts live in `channel/takeover_prompts.py`. Title parsing lives in `channel/takeover_title.py`.

## Core promise

Explain how a company, brand, product, platform, person, or industry player went from ordinary, late, or one-of-many to dominating its category.

The central question is: **HOW DID THEY GET SO POWERFUL?**

The viewer should finish thinking: I knew they were huge, but I didn't realize THAT was how they won.

This is **not** a How They Really Make Money episode. A money-model cut asks where profit comes from. A takeover cut asks what changed so they won. Some overlap is fine. The narrative question is different.

## Sacred rules

These are non-negotiable on every How They Took Over title (and the same bar applies on the other two channels):

1. **Fresh research for every video.**
2. **Different story architecture** for each company.
3. **Original narration, not rewritten articles or YouTube transcripts.**
4. **Unique scenes and diagrams** built around that company's actual business.
5. **unique story engine** — one object / place / reversal that would not work on any other cut.

If you could swap the names and keep the same video, throw it out. Other YouTube videos are competitive research, not sources or scripts.

## The transformation

Every episode is a **transformation**, not a corporate biography.

Do **not** structure episodes as founded in X → founder biography → product list → revenue today.

Identify: the initial problem, the bet, the turning point, the enemy, the breakthrough, the flywheel, the moat, the moment they pulled away, the threat, the real reason they won.

The title analyzer must **not** assume the hidden advantage (CUDA, Prime, scarcity, etc.). starting_position, dominant_position, competitors, and possible_hidden_advantage stay `unknown until researched` until sources confirm them.

Titles do **not** have to be "How X Took Over Y". "How Rolex Became the Ultimate Status Symbol", "How Amazon Built an Empire", and "Why Everyone Started Using Zoom" are all valid. "How Nvidia Really Makes Money" is the other channel — use `--channel behind_the_business`.

## Length and voice

- Target **18–25 minutes** (preferred about 21–23; 1080–1500 seconds). Prefer 16 excellent minutes to 24 padded minutes.
- Kokoro speed **1.15** (never below **1.0** on a new title).
- Script **2800–3600 words**. Write spoken English at about 145–155 wpm. Do not pad a thin story to hit 25 minutes.
- Stills change every **4–8 seconds**. Complex flywheels may hold longer if they evolve.
- Voice: a smart friend explaining how an empire was built. Not an MBA lecture, not Wikipedia, not financial TV, not TikTok hype.

## Research

Before writing: annual reports, SEC/equivalent, shareholder letters, investor decks, official archives, founder/executive interviews, earnings calls, court/regulatory documents when relevant, then reputable journalism and biographies. Wikipedia is a seed only. Other YouTube videos are competitive research, not sources.

Never invent numbers, quotes, market share, motives, meetings, or competitor reactions. Store `source_date` / `fiscal_period` / `data_date` on important claims. If motive is inferred, say "This appears to have…" or "The strategy suggests…".

Fill `project.takeover`: starting vs current position, ranked turning points, fair competitor map, flywheels with ordered steps, moats, threats, dominance forces (several may apply), archetype, related next subject.

No investment advice.

## Story movement (guidance, not a stamp)

World before → underdog → the bet → first breakthrough → the war → turning point → flywheel → pulled away → why it was hard to stop them → the threat → the title answer.

Research picks the archetype (`channel/takeover_visuals.py`). Never force UNDERDOG_TO_DOMINANCE onto a luxury brand or a slow compounder. Nvidia's graphics→ecosystem→AI explosion is not Rolex's credibility→scarcity→status.

Cold open (0:00–0:30): where they started, where they ended up, why that gap is surprising. NEVER "X was founded in…".

Retention: something new every 20–40 seconds; a major reveal every 60–120 seconds; a real shift around 5 / 10 / 15 / 20 minutes. `channel/takeover_qa.py` checks 60-second segments, dead sections (founder bio, product lists, MBA jargon, generic small→launch→win), and virality floors (hook / curiosity / story_depth ≥ 8, title payoff ≥ 9).

## Visuals

`HOW_THEY_TOOK_OVER_VISUAL_STYLE` is frozen in `channel/config.py`: clean modern flat 2D, energetic, strategic, flywheels, competitor maps, timelines. Not the muted historical What They Really Think palette. Not the money-flow How They Really Make Money grammar. Not photoreal. Not 3D corporate. Not logo vs logo.

Rotate `TAKEOVER_VISUAL_TYPES`. Reveal flywheels progressively. Animate timelines date → event → date. Competitor scenes show the strategic difference. One chart = one idea.

Company names stay out of image prompts.

## Shorts, thumbs, metadata

- One Short per long video: **30–55 seconds**, one turning point, not a 22-minute compress.
- Thumbnail: before→dominance or subject vs competition or secret advantage, **2–5 words**, no lying.
- YouTube copy uses the How They Took Over attribution and an educational + synthetic-media disclosure.
- Channel handle: **@HowTheyTookOver**. Profile **800×800** JPEG and cover **2560×1440** JPEG (`python -m channel branding --channel how_they_took_over --profile … --cover …`). Paste `assets/youtube/how_they_took_over_about.txt` into the channel About box. Cover art must keep the story in the center 1546×423 safe band (do not upload the safe-zone preview).
- After assemble: `python -m channel youtube <slug>`.
- Originality compares against `docs/takeover/README.md` (last 10 takeover videos), not against Freud, Einstein, Visa, or Costco.

## Pipeline

```text
 1. Read this file + docs/takeover/README.md (do not copy a shipped rise).

 2. .venv/bin/python -m channel init --channel how_they_took_over "<title>"
    Optional: --instructions "..." --duration 1320 --skip-seed
    Writes channel/projects/<slug>/project.json with channel_mode set.

 3. RESEARCHER using channel/takeover_prompts.py. Fill research.claims from
    primary sources. Fill project.takeover (gap, turning points, competitors,
    flywheels, threats). Never invent numbers. Do not assume the hidden bet.

 4. .venv/bin/python -m channel qa <slug>
    Fix rejected claims. Do not write narration until factcheck is honest.

 5. STORY + NARRATION (2800–3600 words, transformation spine, title_payoff in the VO).
    BIBLES: visual_identity; names stay out of image prompts.

 6. .venv/bin/python -m channel chunks <slug>
    One Scene per line. Rotate TAKEOVER_VISUAL_TYPES.

 7. .venv/bin/python -m channel qa <slug>
    Need originality_score ≥ 80 vs docs/takeover/ and ready_to_publish
    (includes transformation_depth).

 8. .venv/bin/python -m channel compile <slug>
    Then GenerateImage stills + thumbs. Assemble. youtube pack.
    When it ships: docs/takeover/<slug>.md + docs/takeover/README.md.
```

Optional: `python -m channel score-title --channel how_they_took_over "<title>"` and `python -m channel suggest-titles --channel how_they_took_over "<subject>" --y "<arena>"`.
