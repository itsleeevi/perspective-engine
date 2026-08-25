# Videos produced

Index of fixture-driven YouTube cuts. Each page is the memory for the next agent: spine, what not to reuse, paths, voice.

When you finish a new video, add a page here and link it. Keep each page's **"## Do not copy"** section stocked with *quoted* phrases — `scripts/lint_story.py` reads those quotes and blocks any new script that reuses them.

- [What Elon Musk Really Thinks About Sam Altman](elon-musk-sam-altman.md) — channel engine, empty wooden chair / Honest Thoughts / ChatGPT / xAI next door / 2026 clock, Kokoro `am_liam`, **21:40** (facts through August 2026; no “today is DATE” in the VO)
- [What Freud Really Thought About Women](freud-women.md) — channel engine, Dora folder / little-man map / Horney's no / dark continent, Kokoro `am_michael`, **24:56** (facts through August 2026; no “today is DATE” in the VO)
- [What Darwin Really Thought About Human Nature](darwin-human-nature.md) — channel engine, Notebook B fork / Jemmy Button / Descent of Man, Kokoro `am_liam`, ~8 min (facts through August 2026; no “today is DATE” in the VO)
- [What Jeff Bezos Really Thinks About Elon Musk](jeff-bezos-elon-musk.md) — channel engine, tortoise / hare / Blue Origin / SpaceX / New Glenn, Kokoro `am_liam`, ~8 min (facts through August 2026; no “today is DATE” in the VO)
- [What Elon Musk Really Thinks About AI](elon-musk-ai.md) — channel engine, MIT demon / OpenAI / Grok / SpaceX, Kokoro `am_liam`, ~8 min (facts through August 2026; no “today is DATE” in the VO)
- [What Sam Altman Really Thinks About the Future of Work](sam-altman-the-future-of-work.md) — channel engine, inbox / 2021 essay / Senate / the check, Kokoro `am_liam`, ~8 min
- [What Steve Jobs Really Thought About Bill Gates](steve-jobs-bill-gates.md) — channel engine, 1983 room / Xerox / 1997 screen, Kokoro `am_liam`
- [What Einstein Really Thought About Religion](einstein-religion.md) — channel engine, telegram / letter split, Kokoro `am_liam`
- [What Stalin Really Thought About Hitler](what-stalin-really-thought-about-hitler.md) — v4 Simple History-like flat vector, faster Michael, explain-like-five (`the_thought`)
- [What Hitler Really Thought About Americans](what-hitler-really-thought-about-americans.md) — v4 perspective story, silent chapter cards, Kokoro `am_liam`. The v4 storyboard fails the current prop-economy linter (book in 47/77 frames); any rewrite must pass `lint_storyboard.py` and use Kokoro (never Edge or ElevenLabs).
- Putin-Americans lives in git history (`fixtures/putin_americans.json`); do not reuse that clap/coupon/machine spine.

Playbook: [`docs/custom-videos.md`](../custom-videos.md) — new titles start with `python -m channel generate --channel what_they_really_think --title "What X Really Thought About Y"` (isolated `artifacts/<JOB_ID>/`). Sequential local still has `python -m channel init`. New long cuts are **20–25 minutes** (4400–5500 words). Do not copy a shipped spine. **originality_score ≥ 80** vs the last 10 videos and **`ready_to_publish`** before stills. Named public figures reuse `channel/character_locks.json`. YouTube descriptions include an honest synthetic-media disclosure. Shorts description is `Watch the full video:` / `https://youtu.be/<id>` / punch paragraph / disclosure.
