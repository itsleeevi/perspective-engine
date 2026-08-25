# Originality and monetization

Thresholds live in `channel/originality_policy.py`. Do not restate them only in chat.

- Compare the last **10** videos on **this** channel (`docs/videos/`, `docs/business/`, or `docs/takeover/`).
- `originality_score >= 80`
- `ready_to_publish` before GenerateImage
- Brand (flat 2D, channel name, Kokoro, title pattern) is ignored
- Name-swap spines fail
- Stock hooks / endings / generic AI phrases fail

Money jobs also need `financial_accuracy` and `business_analysis_depth`. Takeover jobs need `transformation_depth`.

Retention: something new every 20–40 seconds; a reveal every 60–120 seconds; a shift around 5 / 10 / 15 / 20 minutes. Channel QA modules enforce dead sections.

Human value test: would this still look researched if the tools were hidden? If no, revise.

Quality bar (`docs/video-engine/QUALITY_BAR.md`): copy the grammar of the best-performing uploads (kid map, recognizable cartoon locks, oversized stills, punchy Shorts). Never copy their spines. Same quality, new story.
