# How They Took Over

Internal mode: `how_they_took_over` (aliases: `htto`, `takeover`, `took_over`).
Playbook: `docs/how-they-took-over.md`. Config: `HOW_THEY_TOOK_OVER`.
Prompts: `channel/takeover_prompts.py`. Index after ship: `docs/takeover/`.

This is **not** a money-model episode. Overlap is fine; the question is transformation.

## Channel promise

**How did this company / brand / technology become so powerful?** Viewer finish: I knew they were huge, but I didn't realize THAT was how they won.

## Target audience

People who already know the name and want the rise, the war, and the moment of separation — not a corporate timeline.

## Runtime and narration length

| | Value |
|---|---|
| Runtime | 18–25 minutes (prefer ~21–23; 1080–1500s, target 1320) |
| Script | **2800–3600** words |
| Spoken pace | 145–155 wpm; Kokoro **1.15** (never below **1.0** on a new title) |
| Voice | Kokoro `am_liam` (roster may rotate) |
| Padding | Prefer 16 excellent minutes to 24 padded minutes |

## Narration personality

Smart friend explaining how an empire was built. Energetic but professional. Not MBA, not Wikipedia, not financial TV, not TikTok hype.

## Story architecture

```text
world before → starting position → strategic bet → breakthrough → competition
→ turning points → flywheel → moment of separation → moat → current threat
→ real reason they won
```

Do **not** write founded-in → founder biography → product list → revenue today. Research picks the archetype. Analyzer must **not** assume CUDA, Prime, scarcity, or any hidden advantage from the title (`unknown until researched`).

## Research priorities

Filings, archives, founder/executive interviews, earnings calls, court/regulatory documents when relevant, technical papers when the bet is technical, then reputable journalism. Fair competitor map. Ranked turning points. Never invent numbers, quotes, market share, or meetings.

## Title interpretation

How X Took Over Y / Became… / Built an Empire / Why Everyone Started Using…  
“How Nvidia Really Makes Money” is the other channel — raise and point to `behind_the_business`.  
A Think title here is wrong — point to `what_they_really_think`.

## Scene grammar

Flywheels, competitor comparisons, maps, before/after environments. 6–10 chapters. Unique to that takeover. Not BTB money-flow desks. Not muted WTRT portraits.

## Visual identity

`HOW_THEY_TOOK_OVER_VISUAL_STYLE`: clean energetic strategic flat 2D, high readability, strategy diagrams, timelines, maps, flywheels. Not photoreal, 3D, anime, or stock.

## Thumbnail strategy

Before→dominance or secret advantage. 2–5 words. Default overlay `WHY THEY WON`. Empty right third. No on-image text in the still.

## Short strategy

One turning-point image, 75–140 words, branded end card, link in description.

## Retention

New every 20–40 seconds. Title payoff ≥ 9. Transformation must stay the spine. `channel/takeover_qa.py` flags dead sections and claim flags.

## Originality and monetization

Score vs last 10 in `docs/takeover/`. Need `transformation_depth`. Do not clone Nvidia’s CUDA story onto Rolex.

## QA thresholds

`originality_score ≥ 80`, `ready_to_publish`, factcheck, takeover QA ready. No GenerateImage until those pass.
