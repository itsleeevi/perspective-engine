# What They Really Think

Internal mode: `what_they_really_think` (aliases: `wtrt`, `think`).
Playbook: `docs/custom-videos.md`. Config: `CHANNEL` in `channel/config.py`.
Prompts: `channel/agent_prompts.py`. Index after ship: `docs/videos/`.

This is **not** a 4–6 minute format. Older shipped cuts were shorter. **New titles are ~20–25 minutes, 4400–5500 words at Kokoro 1.15.**

## Channel promise

Answer “What did X really think / really thinks about Y?” through one story. The viewer should finish able to repeat `the_thought`.

## Target audience

People who click a mystery-opinion title and want a blunt cartoon-clear story an adult still enjoys.

## Runtime and narration length

| | Value |
|---|---|
| Runtime | ~20–25 minutes (1200–1500s, target 1380) |
| Script | **4400–5500** words |
| Spoken pace | write 145–155 wpm; Kokoro **1.15** (never below **1.0** on a new title) |
| Voice | Kokoro `am_liam` (roster may rotate `am_michael` / `am_fenrir`) |
| Stills | new composition every 4–8 seconds (target 6.5s) |

## Narration personality

Calm, curious, intelligent friend telling history. Slightly mysterious. Simple spoken English, third person. Not baby talk, not a lecture, not Wikipedia.

Calendar years as digits (`1995`). No “today is DATE”. `the_thought` is said in the VO.

## Story architecture

```text
QUESTION → EVIDENCE → CONTRADICTION → DEVELOPMENT → DEEPER ANSWER → TITLE PAYOFF
```

Do **not** generate a generic biography. Biography is allowed only when it explains **why X thought this about Y**.

Banned cold opens: “Month Year. Name was born…”. Unique story engine required (`lint_story.py`).

## Research priorities

Primary sources first: letters, speeches, interviews, notebooks, official documents, then reputable biographies. Wikipedia is a seed only. Never invent quotes. Scenes carry `source_claim_ids`.

## Title interpretation

`What {subject} Really {Thought|Thinks} About {target}`. Pass `--channel what_they_really_think`. Do not route a money or takeover title here.

## Scene grammar

One still per narration chunk. 4–6 chapters. ONE signature prop in ≤ 6 scenes, obvious when it returns. Empty / hero / crowd rotation. Names out of image prompts.

## Visual identity

`GLOBAL_VISUAL_STYLE`: simple flat 2D historical educational illustration, vector-like, simplified anatomy, simple faces, muted historical palette, limited gradients. Not photoreal, 3D, anime, watercolor, oil, or cinematic photography. Face-fill thumbs, empty right third for type added later.

## Thumbnail strategy

Tight chest-up of the subject. Face ≥ 30% of frame. 2–5 words overlay burned after GenerateImage. No on-image text in the still. 1280×720 JPEG.

## Short strategy

One ironic moment, 30–55s (about 60–135 words). Ends on branded card: watch the full video, link in the description. Captions in the YouTube safe band.

## Retention

Something new every 20–40 seconds. A real shift around 5 / 10 / 15 / 20 minutes. `the_thought` spoken. Mechanical QA threshold 8.

## Originality and monetization

`originality_score ≥ 80` vs last 10 in `docs/videos/`. `ready_to_publish` before GenerateImage. Name-swap spines fail. Brand look is not a fail.

## QA thresholds

`python -m channel qa`. Factcheck ok. Title payoff in VO. `lint_story.py` + `lint_originality.py`. Ready means scores + originality + monetization all pass.
