# What Einstein Really Thought About Religion

Channel-engine cut (`python -m channel init`). Do not clone this spine for a different title.

## Spine

Third-person documentary. `the_thought`: **He thought God was the order of the universe, not a person who listens.** Cold open names Einstein, religion, the contradiction, and that sentence. Silent cards: **The Telegram** → **The Door** → **The Nickname** → **The Letter** → **The Feeling**.

A rabbi pays for fifty words. Einstein cables Spinoza's God, not a God who meddles. As a boy he was devout, then science books ended it. He would not stop saying God: dice, the Old One, a child in a library. Near the end he writes that the word God is human weakness. Same split, twenty-five years apart. Cosmic religious feeling is the name he gives the awe. He will not kneel and will not enlist in the war on kneeling.

## Do not copy onto the next title

- “He thought God was the order of the universe, not a person who listens”
- “They were reading two different men”
- The paid telegram / fifty words / Spinoza cable as the only cold open
- “A slammed door that still makes a noise”
- “God is a nickname for the law”
- The child in the unread library as the only humility image
- “He would not kneel, and he would not enlist in the war on kneeling”
- Stalin toast / child's deal / rented wolf
- Hitler five-fakes / cowboy book

## Technical

| | |
|---|---|
| Project | `channel/projects/einstein-religion/project.json` |
| Fixture | `fixtures/einstein-religion.json` |
| Stills | `fixtures/einstein-religion_stills.py`, jobs `fixtures/einstein-religion_v1_image_jobs.json` |
| Spec | `fixtures/video_specs/einstein-religion.json` |
| Voice | Kokoro `am_liam`, speed 1.15, one utterance per scene + 0.28s hold, burned-in captions |
| Output | `assets/output/what_einstein_really_thought_about_relig_final.mp4` (3840×2160, **3:29**, ~85 MB) |
| Sync | cut error 16.67 ms (half a 30 fps frame) |
| Short | `assets/output/einstein-religion_short.mp4` (1080×1920, **22.0s**, cut error 14.67 ms) |
| Thumb | `assets/youtube/einstein_religion_thumbnail_1280x720.jpg` (1280×720, overlay **NOT THAT / GOD**) |
| Description | `assets/youtube/einstein_religion_description.txt` |
| Short description | `assets/youtube/einstein_religion_short_description.txt` |
| Tags | `assets/youtube/einstein_religion_tags.txt` |
| Thumb job | `fixtures/einstein-religion_thumbnail_image_jobs.json` |

Signature prop: THE_LETTER in 5 long scenes. No historical names in image prompts.

## YouTube pack

Refresh with `python -m channel youtube einstein-religion` (assemble JSON stamps chapter times). Upload the JPEG, not the 3:2 PNG.

**Title:** What Einstein Really Thought About Religion

**Short title:** Why Einstein's God Letter Still Fools People

**Thumbnail text:** NOT THAT / GOD

**Description** (search phrase in the first 200 characters):

```
What Einstein really thought about religion: he thought God was the order of the universe, not a person who listens.

In 1929 a rabbi paid for a yes he could print. Einstein cabled Spinoza's God — the lawful harmony of the world, not a God who meddles. Churches quoted him. Atheists quoted him. They were reading two different men.

Twenty-five years later a handwritten letter called the word God a human weakness. Same split. Same man. This illustrated documentary from What They Really Think tells that story.

0:00 Intro
0:13 The Telegram
0:46 The Door
1:20 The Nickname
2:03 The Letter
2:46 The Feeling

Synthetic media: images and narration are generated. Not a photograph of any real person.
```

**Tags:** einstein, einstein religion, what einstein really thought about religion, spinoza, spinoza's god, cosmic religious feeling, 1929 telegram, gutkind letter, albert einstein documentary, illustrated documentary, what they really think, history of science, einstein god

## Playbook

`docs/custom-videos.md`
