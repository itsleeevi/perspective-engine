"""
Provider-agnostic prompt text for the two authoring calls (script writing,
storyboard visualization).

The prompt content is where the actual behavioral fixes for this format live
(duration-vs-clock, cast consistency, flag avoidance, ...); it is shared
verbatim between every LLM provider adapter so a fix made once benefits
whichever model is currently configured, instead of drifting out of sync
between an Anthropic copy and an OpenAI copy of the same instructions.
"""

from __future__ import annotations

from graph.script_fixture import NARRATION_WPM

# Shot types the storyboard prompt may choose from. The three character-free
# ones must match graph.style's expectations via
# adapters.llm.base.CHARACTER_FREE_SHOT_TYPES (asserted where imported), so a
# rename here cannot silently start appending the hero to object shots again.
SHOT_TYPES = (
    "medium shot",
    "wide shot",
    "two-person shot",
    "extreme close-up",
    "top-down flatlay",
    "symbolic graphic",
)

# Beats per visualize_beats call. Large enough to keep the call count (and so
# the cost) low, small enough that the model does not start truncating or
# losing track of the ordering. 16 is safe once reasoning is disabled: the
# completion budget is spent on JSON, not hidden thinking tokens that used
# to truncate the last scenes of a batch.
VISUALIZE_BATCH = 16

# Beats of preceding narration each batch sees as read-only context, so the
# first shot of a batch knows what room the story is standing in.
VISUALIZE_LEAD_IN = 3

# Bumped whenever either prompt's required structure or instructions change
# meaningfully, so a prompt fix (or a provider swap) doesn't silently keep
# serving a stale cached result written under the old wording.
WRITE_SCRIPT_PROMPT_VERSION = 7
VISUALIZE_BEATS_PROMPT_VERSION = 11


def write_script_system_prompt() -> str:
    """
    Static format rules for the career-ladder script. Kept as its own string
    so the OpenAI adapter can send it as a system message (models weight
    that more reliably than burying the same rules under the topic).
    """
    return (
        "You write narrated, second-person 'career ladder' video scripts.\n\n"
        "FORMAT — every video in this series follows the same structure:\n"
        "- Premise: 'your life as every level/rank of X'. The viewer is cast "
        "as the hero, addressed as 'you', living through 8 to 10 escalating "
        "stages of the career, role, or hierarchy the title implies.\n"
        "- Each stage is a LEVEL with a short role name (2-4 words, e.g. "
        "'The Applicant', 'The Trainee', 'The Team Leader') and its own "
        "block of narration.\n"
        "- A 1-2 sentence HOOK opens the video before the first level: a "
        "cold-open statistic or stark statement of stakes, no 'you' yet.\n"
        "- Narration is second person ('you'), present tense, dry factual "
        "documentary-explainer tone — never melodramatic. Vary sentence "
        "length, short and blunt mixed with longer ones. Use specific, "
        "concrete, plausible sensory and numeric detail (times, distances, "
        "ages, dollar amounts, durations, counts) — vague generalities read "
        "as filler.\n"
        "- Each level escalates the responsibility, stakes, and personal "
        "cost of the last. Attrition/washout framing ('most people don't "
        "make it this far') suits early levels; personal and relationship "
        "cost suits late ones.\n"
        "- The FINAL level loops back to the start: someone new begins the "
        "exact journey the hero just finished, unaware of what is ahead, "
        "closing on a one-line thematic callback ('the cycle continues').\n"
        "- The hero is a fictional composite everyman, never a real, named, "
        "identifiable individual — even when the topic names a real "
        "organization or role.\n"
        "- Write PLAIN narration only: no scene directions, no camera "
        "language, no markdown or headings inside the beats themselves.\n"
        "- Never write a clock time as a bare digit cluster ('0500', '2200', "
        "'0500 hours'). Text-to-speech reads that as isolated digits ('oh "
        "five zero zero') instead of a time. Spell it the way it would "
        "actually be said aloud: 'five in the morning', '5 a.m.', 'ten at "
        "night'. The same goes for any other number a reader would normally "
        "sound out as a unit (phone extensions, serial-style codes) rather "
        "than read digit by digit.\n"
        "- After drafting, silently count the narration words per level and "
        "cut the weakest sentence in any level that overruns its cap. Never "
        "drop a level or end the story early to make the count fit.\n\n"
        "Return ONLY valid JSON in exactly this format (no extra text):\n"
        '{"hook": "...", "levels": [{"name": "The Applicant", "beats": '
        '["paragraph one of narration", "paragraph two", "..."]}, "..."]}\n\n'
        "Each level's \"beats\" list should have 2 to 5 paragraphs, each "
        "paragraph 2 to 5 sentences: long enough to sustain the level, "
        "short enough to keep momentum."
    )


def write_script_user_prompt(topic: str, brief: str, target_minutes: float) -> str:
    """Per-run topic, brief, and word-budget instructions."""
    length_rule = ""
    if target_minutes > 0:
        budget = round(target_minutes * NARRATION_WPM)
        # The total word ceiling is what actually controls runtime; the
        # level count only decides how the same words are divided up. Asked
        # for 10 levels instead of 8 at the same ceiling, the model wrote the
        # same ~1280 words spread thinner (and threw in an eleventh level),
        # so 8 meatier levels is the better structure at any length this
        # format is used for.
        levels = 8
        per_level = round(budget / levels)
        length_rule = (
            f"LENGTH — this script is spoken at {NARRATION_WPM:.0f} words "
            f"per minute and must not run past {target_minutes:.0f} "
            f"minutes, so {budget} words of narration is a HARD CEILING "
            "for the whole script, not a target to drift past. Use "
            f"exactly {levels} levels of AT MOST {per_level} words each; "
            "count as you go and cut the weakest sentence whenever a "
            "level runs over. Stay inside the ceiling by making each "
            "level tighter and more selective, NOT by dropping levels or "
            "ending the story early — the full arc, including the "
            "closing loop back to the beginning, still has to fit.\n\n"
        )
    extra = "" if length_rule else " Use 8 to 10 levels total.\n\n"
    return (
        "Write a narrated, second-person 'career ladder' video script for "
        f'the YouTube video titled: "{topic}"\n\n'
        f"Additional brief (may be blank): {brief}\n\n"
        + length_rule
        + extra
        + "Follow the format rules exactly."
    )


def write_script_prompt(topic: str, brief: str, target_minutes: float) -> str:
    """
    Combined script prompt for providers that send a single user message.

    ``target_minutes`` sizes the whole script to a runtime by converting it
    into a word budget at the measured narration rate. Length has to be
    controlled *here*, at the writing step: capping levels afterwards would
    drop the final level, and the final level is the one that closes the
    loop back to the beginning.
    """
    return (
        write_script_system_prompt()
        + "\n\n"
        + write_script_user_prompt(topic, brief, target_minutes)
    )


def visualize_system_prompt() -> str:
    """
    Static storyboard rules. Identical across every batch of a run so the
    OpenAI adapter can cache them (the rules alone are well over the
    1,024-token cache-prefix minimum).
    """
    shot_types = ", ".join(f"'{t}'" for t in SHOT_TYPES)
    return (
        "You are the storyboard artist for a narrated 'Your Life As Every "
        "Rank/Level of X' explainer channel (think faceless YouTube "
        "channels that illustrate every line of narration literally, in "
        "a detailed graphic-novel style — a folding table with a visible "
        "price sticker, a laptop with dust in its fan vents, a roommate's "
        "comic-book 'SNORT! ZZZ!' sound effects). Each numbered fragment "
        "is a 3-4 second slice of narration that will be spoken over ONE "
        "illustration. Write the illustration brief for each fragment.\n\n"
        "Rules:\n"
        "- Write in THIRD PERSON as an outside observer: 'a young man signs "
        "papers at a desk…'. Never use 'you' or 'your'.\n"
        "- The illustration must show THE MOMENT ITS FRAGMENT DESCRIBES, in "
        "the place the surrounding fragments have established. The "
        "fragments are consecutive: read them as one continuous scene and "
        "change location only where the narration itself moves ('three "
        "weeks later', 'back home', 'on day one'). A fragment in the "
        "middle of an interview must stay in that interview room. This is "
        "the rule most often broken, and a viewer notices instantly when "
        "the picture wanders off somewhere the narration never went.\n"
        "- READ NUMBERS FOR WHAT THEY ARE. A DURATION is an amount of "
        "elapsed time, not a clock reading and not a date: 'the interview "
        "lasts 22 minutes' must never become a clock showing '22:00', "
        "'six weeks of training' must never become the number 6 on a "
        "wall. Most durations have nothing to draw — illustrate the "
        "moment instead (the agents still writing, the applicant still "
        "waiting) and leave the number out entirely. Only put a number in "
        "frame when the fragment names something that genuinely carries "
        "it: a price on a tag, a score on a form, a room number on a "
        "door. This applies even when it is tempting to reuse the "
        "duration's own digits as a clock reading ('the interview lasts "
        "22 minutes' becoming a clock showing '11:22') — that is still a "
        "wall clock claiming to show what time it is, and it is wrong in "
        "exactly the same way.\n"
        "- A prop that DISPLAYS a number — a clock, a timer, a "
        "scoreboard, a speedometer, a receipt — must either show the "
        "exact value the fragment gives, quoted, or stay out of the "
        "frame. Asking vaguely for 'a nightstand clock' over a line "
        "about a call at 11:50 p.m. produced a clock reading 2:37, which "
        "is not a small error: the one thing in the shot a viewer can "
        "read contradicts the sentence being spoken over it.\n"
        "- Avoid national flags, government seals, service crests, and "
        "currency as prominent elements. Their exact geometry is fixed "
        "and public, so any error reads as a mistake rather than as "
        "stylisation; a flag drawn with the wrong number of stars is the "
        "only thing a viewer will look at. Establish an official setting "
        "with things that have no canonical form instead — a panelled "
        "wall, a heavy wooden desk, a framed photograph of a domed "
        "building, a lanyard, a metal detector. If a flag is unavoidable, "
        "keep it small, furled on a stand, or cropped by the frame edge.\n"
        "- ONE recurring protagonist runs through the whole video: the man "
        "the narration's 'you' refers to. Any shot containing a person "
        "must have HIM as its subject. Never write a shot whose only "
        "person is somebody else ('the interviewer studies his notes') — "
        "he is the one drawn as the recurring character, so a shot like "
        "that silently recasts him as the wrong person. Show the other "
        "character only alongside him, or cut to an object instead.\n"
        "- NEVER describe the protagonist's head, face, hair or age. His "
        "design is fixed and supplied separately; 'a gray-haired man', "
        "'an older man', 'a young man with a beard' contradict it, and "
        "the render splits the difference and hands the video a "
        "different-looking lead halfway through. Call him 'the man' and "
        "describe only his clothing, posture and action. Age and rank are "
        "conveyed by what is around him — the office, the suit, the "
        "people deferring to him — not by his face. (His clothing IS "
        "allowed to carry rank markers appropriate to the level — "
        "insignia, a better-tailored uniform, a bigger office — that is "
        "handled separately and escalates on its own; just don't touch "
        "his face or age.)\n"
        "- Keep the cast small: him, plus at most one or two others. Do "
        "not call for crowds of dozens or hundreds of individuals; a "
        "packed room is better described as 'rows of seated figures "
        "receding into the background'.\n"
        "- Be LITERAL and CONCRETE, not generic. Illustrate the fragment's "
        "specific nouns and numbers directly: if it mentions a dollar "
        "amount, an age, a brand-less product, a count, or a named object, "
        "put that exact thing in frame (e.g. 'a folding table with a "
        "$14.99 price sticker still on one leg', not just 'a table'). "
        "This is the single most important rule — a description that "
        "would fit ten different fragments equally well has failed.\n"
        "- Fill the frame with the setting, not just the subject: name two "
        "or three further props that belong in that place and support the "
        "line (what is on the desk, taped to the wall, stacked on the "
        "floor, visible through the window).\n"
        "- Pick ONE shot type per fragment and return it in the "
        f"'shot_type' field, spelled exactly as one of: {shot_types}.\n"
        "    * medium shot — the man from the waist up, doing the action, a "
        "detailed background behind him\n"
        "    * wide shot — a location or environment, the man small inside it, "
        "full of small concrete props that tell the story\n"
        "    * two-person shot — the man and one other character interacting\n"
        "    * extreme close-up — NO PEOPLE AT ALL: a single object or detail "
        "filling the frame (a dusty laptop vent, a price tag, a clock face, "
        "a cluttered desk corner)\n"
        "    * top-down flatlay — NO PEOPLE AT ALL: looking straight down at a "
        "desk or surface and the objects arranged on it\n"
        "    * symbolic graphic — NO PEOPLE AT ALL: a concrete object or "
        "arrangement of objects standing in for an abstract or reflective "
        "line (a locked door, an empty chair, a calendar with dates "
        "crossed off, a single lit window in a dark building). Never a "
        "poster, title card, infographic, or big word-art headline.\n"
        "- The three NO PEOPLE types must not mention the man, a person, a "
        "hand, a body part, or anyone's possessions ('the interviewer's "
        "notepad') anywhere in the description — those shots are rendered "
        "with people explicitly forbidden, so a person implied there comes "
        "out as an off-style stranger. Write 'a notepad on the desk', not "
        "'the interviewer's notepad'.\n"
        "- Vary the shot type across consecutive fragments — do not default to "
        "medium shot every time. Favor extreme close-up and top-down flatlay "
        "for small concrete details; favor wide/medium shots for physical "
        "action; favor symbolic graphics only for genuinely abstract or "
        "reflective lines that have no literal object to show.\n"
        "- In-scene text is allowed but STRICTLY RATIONED: AT MOST ONE "
        "text element per fragment, and only when it genuinely sharpens "
        "the shot — a price tag ('$14.99'), a book spine ('BIOLOGY 101'), "
        "a door sign ('RANGE 4'), a comic-style sound effect ('SNORT!'). "
        "Quote the exact words in single quotes and keep them to four "
        "words or fewer. Most fragments should have NO text at all. Never "
        "ask for a filled-in form, a document, a headline, or several "
        "labels at once: every extra string is another chance for the "
        "image model to misspell something, and a frame on screen for "
        "four seconds cannot be read anyway.\n"
        "- NEVER describe writing without saying what it says. Phrases "
        "like 'a notepad covered in bullet points', 'a screen full of "
        "text', 'a page of handwritten notes' give the image model an "
        "empty slot it will fill with garbage — in one render it "
        "transcribed the prompt itself onto the page. Either quote the "
        "few exact words ('a notepad with 'POLYGRAPH' underlined') or "
        "say the writing is not legible ('a notepad turned away from "
        "the viewer', 'a blurred screen').\n"
        "- Never describe something as ABSENT ('wall clock removed', 'no "
        "photographs on the desk'). An illustrator cannot draw an "
        "absence, and the image model treats the words as things to "
        "include. Name what IS there instead.\n"
        "- Describe only what is VISIBLE: composition, objects, other people, "
        "setting. One to two sentences, under 45 words. No camera jargon, no "
        "art-style or lighting words — those are added separately.\n"
        "- Do not name real people, agencies, or places that would identify a "
        "real individual; keep it a fictional composite.\n\n"
        "Return ONLY valid JSON in exactly this format:\n"
        '{"scenes": [{"beat": 0, "shot_type": "medium shot", '
        '"description": "..."}, {"beat": 1, "shot_type": '
        '"extreme close-up", "description": "..."}]}'
    )


def visualize_user_prompt(
    beats: list[str], topic: str = "", lead_in: list[str] | None = None
) -> str:
    """Per-batch fragments, topic, and continuity lead-in."""
    beats_text = "\n".join(f"  [{i}] {b}" for i, b in enumerate(beats))
    topic_line = f'The video is titled "{topic.strip()}".\n\n' if topic.strip() else ""
    lead_in_text = ""
    if lead_in:
        preceding = "\n".join(f"  {line}" for line in lead_in)
        lead_in_text = (
            "Narration immediately before these fragments, for continuity "
            "only — do NOT write briefs for these lines:\n"
            f"{preceding}\n\n"
        )
    return (
        f"{topic_line}"
        f"{lead_in_text}"
        f"Fragments:\n{beats_text}\n\n"
        f"Return exactly one entry for every fragment 0 to {len(beats) - 1}, "
        "each tagged with its fragment number."
    )


def visualize_chunk_prompt(
    beats: list[str], topic: str = "", lead_in: list[str] | None = None
) -> str:
    """
    Combined storyboard prompt for providers that send a single user message.

    ``shot_type`` is asked for as its own JSON field rather than left
    implicit in the prose because it decides whether the hero description is
    appended to the image prompt at all (see ``graph.style.scene_prompt``).
    """
    return (
        visualize_system_prompt()
        + "\n\n"
        + visualize_user_prompt(beats, topic, lead_in)
    )
