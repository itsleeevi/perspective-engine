"""
Perspective Engine CLI entrypoint.

Usage:
    python -m cli.run "a photon's journey from the sun"
    python -m cli.run --topic "the invention of language"

Loads .env automatically, wires real adapters, runs the full graph, and
handles the two human-review interrupt gates from the terminal.

Interrupt gates
---------------
Gate 1 (human_review_script):  prints script and shot list; prompts for
    approval, rejection, or inline edits before character-ref generation.
Gate 2 (human_review_final):   prints final video path and metadata; prompts
    for approval, rejection, or inline edits before publish.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from typing import Any

# Load .env before importing any adapter (keys must be in os.environ).
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed; rely on pre-set environment variables.

from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command

from adapters.image_gen.fal import FalImageGenAdapter
from adapters.image_gen.mock import MockImageGenAdapter
from adapters.llm.anthropic import AnthropicLLMAdapter
from adapters.llm.mock import MockLLMAdapter
from adapters.video_gen.fal import FalVideoGenAdapter
from adapters.video_gen.mock import MockVideoGenAdapter
from adapters.voice.elevenlabs import ElevenLabsVoiceAdapter
from adapters.voice.mock import MockVoiceAdapter
from graph.graph import build_graph


# ── Interrupt UI helpers ────────────────────────────────────────────────────


def _print_interrupt(iv: dict) -> None:
    """Pretty-print the interrupt payload to stdout."""
    gate = iv.get("gate", "unknown")
    message = iv.get("message", "")
    print(f"\n{'=' * 64}")
    print(f"  INTERRUPT: {gate}")
    print(f"{'=' * 64}")
    print(f"  {message}")

    if "script" in iv:
        print("\n  Script beats:")
        for i, beat in enumerate(iv["script"]):
            print(f"    [{i}] {beat}")

    if "shot_list" in iv:
        print("\n  Shot list:")
        for shot in iv["shot_list"]:
            truncated = shot.get("prompt", "")[:70]
            print(
                f"    [{shot['id']}] mode={shot.get('mode', '?')}  "
                f"prompt={truncated!r}"
            )

    if "final_video_path" in iv:
        print(f"\n  Final video: {iv['final_video_path']}")

    if "metadata" in iv:
        meta = iv["metadata"]
        print(f"\n  Metadata:")
        print(f"    title:       {meta.get('title', '')}")
        desc = meta.get("description", "")
        print(f"    description: {desc[:100]}{'…' if len(desc) > 100 else ''}")

    if "shot_summary" in iv:
        print("\n  Shot summary:")
        for s in iv["shot_summary"]:
            print(f"    [{s['id']}] status={s['status']}  retries={s['retries']}")


def _collect_edit() -> dict:
    """Prompt the user for a single field edit and return it as a dict."""
    field_path = input("    Field path (e.g. 'script', 'metadata.title'): ").strip()
    raw_value = input(
        "    New value (JSON if complex, plain string otherwise): "
    ).strip()
    try:
        new_value: Any = json.loads(raw_value)
    except json.JSONDecodeError:
        new_value = raw_value
    note = input("    Note (optional, press Enter to skip): ").strip()
    return {"field_path": field_path, "new_value": new_value, "note": note}


def _prompt_resume(iv: dict) -> dict:
    """
    Interactive terminal prompt for a single interrupt.

    Returns a resume payload dict compatible with the graph's ``interrupt()``
    contract.
    """
    _print_interrupt(iv)
    print()

    while True:
        raw = input("  Approve? [y / n / edit]: ").strip().lower()
        if raw in ("y", "yes"):
            return {"approved": True, "edits": []}
        if raw in ("n", "no"):
            return {"approved": False, "edits": []}
        if raw in ("e", "edit"):
            print("  Enter one edit (repeat 'edit' after resuming for more):")
            edit = _collect_edit()
            return {"approved": True, "edits": [edit]}
        print("  Please enter 'y', 'n', or 'edit'.")


# ── Main pipeline runner ────────────────────────────────────────────────────


async def main(
    topic: str,
    use_cache: bool = True,
    mock: bool = False,
    max_shots: int | None = None,
    static_only: bool = False,
) -> None:
    # Adapters read ADAPTER_CACHE from the environment at call time, so setting
    # it here (before the graph runs) is enough to toggle the disk cache.
    if mock:
        os.environ["ADAPTER_CACHE"] = "0"  # mocks are instant; cache is irrelevant
    elif not use_cache:
        os.environ["ADAPTER_CACHE"] = "0"
        print("Adapter cache DISABLED — every provider call will spend credits.")
    else:
        os.environ.setdefault("ADAPTER_CACHE", "1")

    print(f"\nPerspective Engine — topic: {topic!r}")

    if mock:
        print("Mode: MOCK (no API calls, $0, instant)")
        llm: Any = MockLLMAdapter()
        image_gen: Any = MockImageGenAdapter()
        video_gen: Any = MockVideoGenAdapter()
        voice: Any = MockVoiceAdapter()
    else:
        n = max_shots or 5
        if static_only:
            est = f"~${n * 0.03:.2f} (no video, FLUX stills only)"
        else:
            est = f"~${n * 1.20:.2f}"
        shots_note = f", {n} shot(s)" if max_shots else ""
        print(f"Mode: REAL (live API calls, {est}{shots_note})")
        llm = AnthropicLLMAdapter()
        image_gen = FalImageGenAdapter()
        video_gen = FalVideoGenAdapter()
        voice = ElevenLabsVoiceAdapter()

    print("Building adapters and compiling graph …")

    checkpointer = MemorySaver()
    graph = build_graph(
        llm=llm,
        image_gen=image_gen,
        video_gen=video_gen,
        voice=voice,
        checkpointer=checkpointer,
    )

    config: dict = {"configurable": {"thread_id": "cli-run-main"}}

    print("Running pipeline …\n")
    initial: dict = {"topic": topic}
    if max_shots is not None:
        initial["max_shots"] = max_shots
    if static_only:
        initial["static_only"] = True
    result = await graph.ainvoke(initial, config)

    # Interrupt loop — handles both human-review gates.
    while result.get("__interrupt__"):
        interrupt_obj = result["__interrupt__"][0]
        iv: dict = (
            interrupt_obj.value
            if hasattr(interrupt_obj, "value")
            else interrupt_obj
        )
        resume_payload = _prompt_resume(iv)

        if not resume_payload.get("approved", False):
            print("\nPipeline aborted by reviewer.")
            sys.exit(0)

        result = await graph.ainvoke(Command(resume=resume_payload), config)

    # Final output.
    print()
    print("=" * 64)
    print("  Pipeline complete!")
    print(f"  Final video:  {result.get('final_video_path', 'N/A')}")
    print(f"  Published at: {result.get('last_published_at', 'N/A')}")
    print("=" * 64)


# ── CLI argument parsing ────────────────────────────────────────────────────


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="python -m cli.run",
        description="Perspective Engine — produce a perspective-shift video from a topic.",
    )
    parser.add_argument(
        "topic",
        nargs="?",
        help="Topic for the video (positional).",
    )
    parser.add_argument(
        "--topic",
        dest="topic_flag",
        metavar="TOPIC",
        help="Topic for the video (named flag).",
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help=(
            "Bypass the adapter disk cache and make fresh (paid) provider "
            "calls. By default cached results are reused to avoid re-spending."
        ),
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help=(
            "Use mock adapters — no API calls, no cost, completes in seconds. "
            "Exercises the full graph including interrupts and assembly. "
            "Use this for all development and debugging."
        ),
    )
    parser.add_argument(
        "--shots",
        type=int,
        metavar="N",
        dest="max_shots",
        help=(
            "Limit the pipeline to N shots (default: all 5). "
            "Useful for cheap real-money smoke tests — 1 shot ≈ $1.20."
        ),
    )
    parser.add_argument(
        "--static",
        action="store_true",
        dest="static_only",
        help=(
            "Force all shots to static_pan — skips Seedance video generation entirely. "
            "Uses only FLUX stills + Claude + ElevenLabs. "
            "With --shots 1: ~$0.10 first run, ~$0.05 on cached re-runs."
        ),
    )
    args = parser.parse_args()
    args.topic = args.topic or args.topic_flag
    if not args.topic:
        parser.error("topic is required — pass it positionally or via --topic.")
    return args


if __name__ == "__main__":
    _args = _parse_args()
    asyncio.run(
        main(
            _args.topic,
            use_cache=not _args.no_cache,
            mock=_args.mock,
            max_shots=_args.max_shots,
            static_only=_args.static_only,
        )
    )
