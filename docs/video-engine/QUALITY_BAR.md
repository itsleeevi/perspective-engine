# Quality bar

The production bar is the **grammar** of the best-performing uploads, not their plots. Copy how they are built. Never copy their objects, chapter names, or `the_thought`.

Implemented in `channel/quality_bar.py`. Stage prompts in `channel/agent_prompts.py`, `channel/business_prompts.py`, and `channel/takeover_prompts.py` point here. `lint_storyboard.py` and `channel/qa.py` fail wallpaper and repeated stills.

```text
Copy the GRAMMAR. Never copy the SPINES.
```

## Reference cuts (grammar only)

Long videos:

| Title | Channel | Grammar to copy | Spine to never copy |
|---|---|---|---|
| What Elon Musk Really Thinks About Sam Altman | Think | Two distinct cartoon faces, kid map of steps, huge returning chair | “He wanted the chair. Sam kept it.” / Honest Thoughts |
| How Tesla Took Over the Electric Car Industry | Takeover | Physical transformation object, fair competitor, ladder of turning points | “They sold a sports car so they could build the charging road.” / one white stall |
| How Costco Really Makes Money | Money | Costume-locked extras, empty cinematic warehouse, decoy till vs real engine | “The card at the door is the real checkout.” / gold card |

Short videos:

| Title | Grammar to copy | Spine to never copy |
|---|---|---|
| How Donald Trump Really Makes His Money | One-sentence slam punch; unique camera every shot; flying clothes/papers; lighting accent + empty margin; recognizable cartoon tycoon | Fat magazine vs thin invoice / blank gold nameplate |
| What Elon Musk Really Thinks About AI | Punch in the first line; oversized signature object filling the frame; hero steps into it | Demon / chalk circle / “builds the machine first” |
| How Elon Musk Really Makes His Money | Number contradiction as the first picture; one lock-object large in frame | 158 billion vs zero / padlocked pay stub |

Tesla fixtures may live under `artifacts/`; the shipped page `docs/takeover/tesla-took-over-the-electric-car-industry.md` is the source of truth for that grammar.

## Story structure

1. Cold open is one **sourced physical contradiction in a specific place**. Not a birth, not a founding, not “Month Year. Name verb…”.
2. Say `the_thought` right after that picture.
3. Give a **kid map of 5–8 steps** this title owns. If a five-year-old can retell those steps, they can retell the video.
4. Silent chapter cards **are those steps**, named from this evidence (not The Suit / The Rocket / The Lab).
5. Each chapter is one step. Cause, then effect. One idea at a time.
6. End by saying `the_thought` again, plus an honest limit (what the papers cannot prove).

`the_thought` is 6–18 words, concrete, child-repeatable. Prefer two beats (“He wanted the chair. Sam kept it.”) over a riddle. Invent a new sentence for this title.

## Characters (heroes)

Named public figures are a **recognizable cartoon of the real person**, not a generic clerk, not a photograph.

1. Look up `channel/character_locks.json`. If the person is there, **copy `visual_lock` exactly** and pass the hashed photo then cartoon sheet in `channel/character_sheets/` as GenerateImage `reference_image_paths`.
2. If they are new, write a lock that starts `Same cartoon person every time, do not redesign. Copy this face:` then face shape, jaw, eyes, hair, stubble or beard, and **ALWAYS-clothes they actually wear** (one outfit, no logos). End with the recognizable-cartoon line. Compile overwrites from the registry when a match exists.
3. A character sheet is three chest-up views (front, three-quarter, profile) on a solid field, hashed filename, no personal name in the file.
4. Two people in one title must not be twins: contrast height, face, and clothes.
5. Expression **changes with the action**. The skull, hair, and ALWAYS-clothes do not.
6. Recurring extras get a **costume lock** (slate sweater shopper, pale blue smock clerk, orange-vest developer). Crowd shots are not gray blobs.
7. Person-titled cuts (Think titles, “makes his/her money”): the named person appears as that cartoon in **about 35–42%** of stills. Company-titled cuts (Costco, Tesla) may run empty cinematic sets; the signature object and extras carry the film.

## Images and scenes

Every still is a cinema beat, not a slide:

```text
{SET} {who/costume} {physical verb} {one oversized focal object} {named lighting}.
Accent: {corner light}, {empty margin}. Unique staging. No logos. No readable type.
```

- **ONE idea** in the frame. **ONE oversized focal object** large in the middle, high contrast, never a faint mark.
- Unique visual verb every still. Ban “Clean business illustration of a filing table” wallpaper and identical desk-and-binder loops.
- Named lighting (warm lamp, cool window, tungsten, night orange). Empty air on one side.
- Fill the entire frame. Rotate composition (wide / medium / close-up / OTS / establishing / object / low / high).
- 12+ locations on a long cut. No set in more than a third of scenes. No three consecutive scenes in the same set.
- Signature prop in at most 6 scenes. When it returns, paste the **same lock sentence**: huge, oversized, high contrast, filling the middle of the frame, never faint, never a tiny version.
- Company and personal names stay out of image prompts and GenerateImage filenames.

`assemble_image_prompt` appends `STAGING_QUALITY` after the frozen channel style. Do not rewrite `GLOBAL_VISUAL_STYLE` / money / takeover identity strings.

## Shorts

- First spoken sentence is the punch (**≤16 words**): a contradiction or a slam, not a definition.
- First still is that picture.
- 6–8 shots, a unique composition each, lighting accent + empty margin.
- Hero cartoon large in frame when the title names a person.
- Last shot is the branded card: “Watch the full video. The link is in the description.”
- Do not spoil the long video’s final button line.

## Originality stays sacred

Same quality, new story. Fresh research. Different architecture. Original narration. Unique scenes. `originality_score ≥ 80` vs the last 10 on **this** channel. `ready_to_publish` before GenerateImage.

If you could swap the names and keep the same video, throw it out — including a name-swap of a reference cut.
