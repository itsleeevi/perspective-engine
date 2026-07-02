"""
Pipeline graph assembly.

``build_graph`` wires all nodes, edges, conditional routing, and the
human-in-the-loop interrupts into a compiled LangGraph ``StateGraph``.

Interrupt behaviour
-------------------
Nodes call ``interrupt()`` to pause; the caller resumes with
``ainvoke(Command(resume=payload), config)``.  No auto-approve path exists.

Fan-out / fan-in  (map-reduce pattern)
---------------------------------------
After ``generate_character_refs`` the conditional edge ``dispatch_shots``
returns ``[Send("process_shot", per_shot_state), ...]`` — one per shot.

Each ``process_shot`` sub-execution handles the complete per-shot lifecycle:
derive still → generate clip (motion) → quality check → retry loop (up to
MAX_SHOT_RETRIES) → approved or escalated.  The retry loop is INTERNAL to
``process_shot``; it is NOT a graph edge.

After every ``process_shot`` finishes, a FIXED edge routes to
``generate_voiceover``.  This matches the canonical LangGraph map-reduce
pattern (``add_edge("generate_joke", "best_joke")``): the barrier fires
only after ALL dispatched tasks have completed because the edge count is
deterministic.  Using a conditional edge (quality_gate → voiceover or
generate_shot) would cause the barrier to fire after the FIRST completion.

``PipelineState.shot_list`` uses the ``_merge_shots`` reducer so all
per-shot updates fan back into the main state automatically.
"""

from __future__ import annotations

import functools
from typing import Any

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from adapters.image_gen.base import ImageGenAdapter
from adapters.llm.base import LLMAdapter
from adapters.video_gen.base import VideoGenAdapter
from adapters.voice.base import VoiceAdapter
from graph.nodes.assemble import assemble
from graph.nodes.generate_character_refs import generate_character_refs
from graph.nodes.generate_metadata import generate_metadata
from graph.nodes.generate_shots import dispatch_shots, process_shot
from graph.nodes.generate_voiceover import generate_voiceover
from graph.nodes.human_review_final import human_review_final
from graph.nodes.human_review_script import human_review_script
from graph.nodes.ideate import ideate
from graph.nodes.publish import publish
from graph.nodes.shot_breakdown import shot_breakdown
from graph.nodes.write_script import write_script
from graph.state import PipelineState


def build_graph(
    llm: LLMAdapter,
    image_gen: ImageGenAdapter,
    video_gen: VideoGenAdapter,
    voice: VoiceAdapter,
    checkpointer: BaseCheckpointSaver | None = None,
) -> Any:
    """
    Compile and return the pipeline StateGraph.

    Parameters
    ----------
    llm, image_gen, video_gen, voice:
        Adapter instances injected via functools.partial.
    checkpointer:
        LangGraph checkpointer.  Defaults to MemorySaver.

    Returns
    -------
    Compiled ``CompiledStateGraph``.
    """
    if checkpointer is None:
        checkpointer = MemorySaver()

    g = StateGraph(PipelineState)

    # ── Bind adapters ──────────────────────────────────────────────────────
    _write_script = functools.partial(write_script, llm=llm)
    _shot_breakdown = functools.partial(shot_breakdown, llm=llm)
    _generate_character_refs = functools.partial(generate_character_refs, image_gen=image_gen)
    _process_shot = functools.partial(process_shot, image_gen=image_gen, video_gen=video_gen, llm=llm)
    _generate_voiceover = functools.partial(generate_voiceover, voice=voice)

    # ── Register nodes ─────────────────────────────────────────────────────
    g.add_node("ideate", ideate)
    g.add_node("write_script", _write_script)
    g.add_node("shot_breakdown", _shot_breakdown)
    g.add_node("human_review_script", human_review_script)
    g.add_node("generate_character_refs", _generate_character_refs)
    g.add_node("process_shot", _process_shot)           # per-shot (via Send)
    g.add_node("generate_voiceover", _generate_voiceover)
    g.add_node("assemble", assemble)
    g.add_node("generate_metadata", generate_metadata)
    g.add_node("human_review_final", human_review_final)
    g.add_node("publish", publish)

    # ── Entry ──────────────────────────────────────────────────────────────
    g.set_entry_point("ideate")

    # ── Linear (pre-generation) ────────────────────────────────────────────
    g.add_edge("ideate", "write_script")
    g.add_edge("write_script", "shot_breakdown")
    g.add_edge("shot_breakdown", "human_review_script")
    g.add_edge("human_review_script", "generate_character_refs")

    # ── Fan-out: one process_shot sub-execution per shot ───────────────────
    g.add_conditional_edges(
        "generate_character_refs",
        dispatch_shots,
        ["process_shot"],
    )

    # Fan-in: FIXED edge (not conditional) from process_shot → generate_voiceover.
    # LangGraph waits for ALL process_shot sub-executions before running
    # generate_voiceover because the edge count equals the number of Sends.
    g.add_edge("process_shot", "generate_voiceover")

    # ── Linear (post fan-in) ───────────────────────────────────────────────
    g.add_edge("generate_voiceover", "assemble")
    g.add_edge("assemble", "generate_metadata")
    g.add_edge("generate_metadata", "human_review_final")
    g.add_edge("human_review_final", "publish")
    g.add_edge("publish", END)

    return g.compile(checkpointer=checkpointer)
