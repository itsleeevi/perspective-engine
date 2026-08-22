# Videos produced

Index of fixture-driven YouTube cuts. Each page is the memory for the next agent: spine, what not to reuse, paths, voice.

When you finish a new video, add a page here and link it. Keep each page's **"## Do not copy"** section stocked with *quoted* phrases — `scripts/lint_story.py` reads those quotes and blocks any new script that reuses them.

- [What Stalin Really Thought About Hitler](what-stalin-really-thought-about-hitler.md) — v4 Simple History-like flat vector, faster Michael, explain-like-five (`the_thought`)
- [What Hitler Really Thought About Americans](what-hitler-really-thought-about-americans.md) — v4 perspective story, silent chapter cards, Kokoro `am_liam`. The v4 storyboard fails the current prop-economy linter (book in 47/77 frames); any rewrite must pass `lint_storyboard.py` and use the Chatterbox voice.
- Putin-Americans lives in git history (`fixtures/putin_americans.json`); do not reuse that clap/coupon/machine spine.

Playbook: [`docs/custom-videos.md`](../custom-videos.md) — new titles start with `python -m channel init "What X Really Thought About Y"`. Do not copy a shipped spine.
