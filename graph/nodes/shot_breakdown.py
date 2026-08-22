"""
shot_breakdown node — turn the script into a structured shot list.

For the level-POV slideshow format the mapping is deterministic and needs no
LLM to decide shot count or timing: one shot per narration chunk, in order.

  - A ``[TITLE]`` beat becomes one locally rendered title card. Rank-show
    cards have their level name narrated over them. Silent chapter cards
    (``[TITLE] (silent) …``) hold ~2.5s of black with no VO, so the heading is
    a visual breath instead of a GPS readout.
  - A narration beat is split into ~3-4 second speaking chunks that begin and
    end on sentence or clause boundaries
    (``script_fixture.split_beat_into_chunks``), so the picture changes
    several times per paragraph and always while the narrator is between
    phrases. Each chunk becomes one shot. The LLM rewrites each chunk as a
    third-person description of the moment to draw (see
    ``LLMAdapter.visualize_beats``); without an LLM a local rewriter stands in.

Every shot's duration starts as a word-count estimate that
``generate_voiceover`` later replaces with the measured length of that
chunk's own audio, so the final cut still lands exactly on the narration.

Every shot is ``static_pan``: this format is a still slideshow, so no
video-generation call is ever made unless a caller explicitly opts into motion.
"""

from __future__ import annotations

from adapters.llm.base import LLMAdapter
from graph import style
from graph.script_fixture import (
    NARRATION_WPM,
    is_title_beat,
    narration_duration_seconds,
    scene_prompt_from_beat,
    split_beat_into_chunks,
    title_card_narration,
)
from graph.state import CostEntry, PipelineState, Shot, ShotMode

_TITLE = "title"
_CHUNK = "chunk"


def _expand_script(script: list[str]) -> list[tuple[str, str]]:
    """
    Expand beat-level script text into per-shot units.

    A title beat is kept whole; a narration beat is split into ~2-3 second
    chunks. Returns ``(kind, text)`` pairs in final shot order.
    """
    units: list[tuple[str, str]] = []
    for beat in script:
        if is_title_beat(beat):
            units.append((_TITLE, beat))
        else:
            units.extend((_CHUNK, chunk) for chunk in split_beat_into_chunks(beat))
    return units


def _shots_from_units(
    units: list[tuple[str, str]],
    style_descriptor: str,
    scenes: dict[int, str],
    character_shots: dict[int, bool],
    hero_career_progression: bool = True,
) -> list[Shot]:
    total_levels = sum(1 for kind, _ in units if kind == _TITLE)
    # -1 until the first title card is seen, so any (unexpected) narration
    # ahead of Level One's card still gets a valid stage rather than a
    # negative index into HERO_CAREER_STAGES.
    level_index = -1
    shots: list[Shot] = []
    for i, (kind, text) in enumerate(units):
        if kind == _TITLE:
            level_index += 1
            spoken = title_card_narration(text)
            shots.append(
                Shot(
                    id=f"shot_{i:03d}",
                    prompt=text.strip(),
                    narration=spoken,
                    is_title_card=True,
                    duration_seconds=narration_duration_seconds(spoken),
                    mode=ShotMode.static_pan,
                    assigned_model="local/title_card",
                )
            )
            continue

        career_stage = (
            style.career_stage_note(max(level_index, 0), max(total_levels, 1))
            if hero_career_progression
            else ""
        )
        scene = scenes.get(i, "")
        prompt = (
            style.scene_prompt(
                scene,
                style_descriptor,
                include_hero=character_shots.get(i, True),
                career_stage=career_stage,
            )
            if scene
            else scene_prompt_from_beat(text, style_descriptor, career_stage=career_stage)
        )
        shots.append(
            Shot(
                id=f"shot_{i:03d}",
                prompt=prompt,
                narration=text.strip(),
                duration_seconds=narration_duration_seconds(
                    text, words_per_minute=NARRATION_WPM
                ),
                mode=ShotMode.static_pan,
            )
        )
    return shots


async def shot_breakdown(state: PipelineState, llm: LLMAdapter) -> dict:
    """
    Build the shot list from the script.

    Returns a partial state update: ``shot_list``, ``cost_log``.
    """
    units = _expand_script(state.script)
    chunk_indices = [i for i, (kind, _) in enumerate(units) if kind == _CHUNK]

    result = await llm.visualize_beats(
        [units[i][1] for i in chunk_indices], topic=state.topic
    )
    scenes = dict(zip(chunk_indices, result.descriptions, strict=False))
    # Object-only shot types (an extreme close-up of a price tag, a top-down
    # flatlay, a symbolic graphic) are rendered without the hero description;
    # see graph.style.scene_prompt for what appending it to those costs.
    #
    # The storyboard's own label is not sufficient on its own. It is instructed
    # never to mention a person in a character-free shot and does so anyway
    # ("the interviewer's notepad, a pen hovers over the page"), which yields
    # the worst outcome of the three: a person in frame with no description of
    # who he is, so the model invents an off-style stranger. Whenever the prose
    # implies a person, the hero goes back in regardless of the label.
    character_shots = {
        unit_index: (
            result.has_character(position)
            or style.mentions_person(result.descriptions[position])
        )
        for position, unit_index in enumerate(chunk_indices)
        if position < len(result.descriptions)
    }

    shots = _shots_from_units(
        units,
        state.character_refs.style_descriptor,
        scenes,
        character_shots,
        hero_career_progression=state.hero_career_progression,
    )

    if not shots:
        raise ValueError("shot_breakdown produced an empty shot list.")

    # Honour the optional shot cap (e.g. --shots 6 for cheap smoke tests).
    if state.max_shots is not None and state.max_shots > 0:
        shots = shots[: state.max_shots]

    if state.static_only:
        shots = [s.model_copy(update={"mode": ShotMode.static_pan}) for s in shots]

    cost = CostEntry(node="shot_breakdown", provider="llm", amount_usd=result.cost_usd)
    return {"shot_list": shots, "cost_log": [cost]}
