# Quiet Wealth

Internal mode: `wealth_pov` (aliases: `quiet_wealth`, `wpov`, `pov_wealth`, `longform_wealth_pov`, `life_pov`, `celebrity_pov`).
Playbook: `docs/wealth-pov.md`. Config: `WEALTH_POV`.
Prompts: `channel/wealth_prompts.py` (`MASTER` is the v13 celebrity and life POV prompt). Index after ship: `docs/wealth/`.

This is **not** a documentary. Second person. Fictional illustrative stories by default. `POV: You Are [Name] From Age X to Y` is a sourced real-person episode with original cartoon stand-ins.

## Channel promise

Let the viewer live through changing circumstances. Ordinary money decisions or a documented life. Finish without pretending a living life is finished.

## Target audience

Adults who want a long illustrated journey with specific stakes, not a list of ages or tips.

## Runtime and narration length

| | Value |
|---|---|
| Runtime | **32–36 minutes** near 34 (1800–2160s, target 2040) |
| Script | **5,600–5,800** words |
| Spoken pace | 165–175 wpm when no sample exists |
| Voice | Gemini 3.1 Flash TTS (`python -m channel tts`); imported audio if no key; Kokoro `am_liam` 1.15 on recuts |
| Chapters | 8–10 substantial eras |
| Shots | meaning-first; ordinary stills 4–7 seconds |

## Narration personality

Warm, observant. Second person. Concrete words. Feeling comes from specific verified detail, never from an emotion label.

## Story architecture

```text
live opening → changing era problems → documented choice points
→ later-era engine in the final third → one close
```

## Research priorities

Fiction: continuity ledger. REAL_PERSON: claims.json per Section 17B. Source only real financial / legal / tax / statistical claims (Investor.gov for index-fund explanations). Never invent private finances of a real named person.

## Title interpretation

`POV: You …` immersive titles. `POV: You Are [Name] From Age X to Y` is documented life. A Think / Money / Takeover title here is wrong — raise and point to the matching `--channel`.

## Visual identity

`WEALTH_POV_VISUAL_STYLE`: v13 detailed 2D narrative cartoon, original stand-ins, pure-white protagonist skin. Not stick-figure doodle.

## Thumbnail strategy

Large original stand-in plus one contrast. 0–4 optional words. Default overlay `THE QUIET CHOICE`.

## Originality and monetization

Score vs last 10 in `docs/wealth/`. Need a filled `project.wealth` ledger or claims register. `originality_score ≥ 80`, `ready_to_publish` before Google Flow.
