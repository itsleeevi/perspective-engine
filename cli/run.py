"""
Perspective Engine CLI entrypoint.

Usage:
    python -m cli.run "a photon's journey from the sun"
    python -m cli.run --topic "the invention of language"

Loads .env automatically, wires real adapters, runs the full graph, and
handles the three human-review interrupt gates from the terminal.

Interrupt gates
---------------
Gate 1 (human_review_script):  prints script and shot list; prompts for
    approval, rejection, or inline edits before character-ref generation.
Gate 2 (human_review_images):  prints each generated still path; prompts
    to approve all or list shot ids to regenerate before voiceover.
Gate 3 (human_review_final):   prints final video path and metadata; prompts
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
from adapters.image_gen.openai_image import OpenAIImageGenAdapter
from adapters.llm.openai_llm import OpenAILLMAdapter
from adapters.llm.mock import MockLLMAdapter
from adapters.video_gen.fal import FalVideoGenAdapter
from adapters.video_gen.mock import MockVideoGenAdapter
from adapters.voice.edge import EdgeTTSVoiceAdapter
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
        if iv.get("gate") == "human_review_images":
            print("\n  Generated stills:")
            for shot in iv["shot_list"]:
                if shot.get("is_title_card"):
                    continue
                still = shot.get("still_url", "")
                if still.startswith("file://"):
                    still = still[len("file://") :]
                status = shot.get("status", "?")
                regen = shot.get("manual_regen_count", 0)
                regen_note = f"  regen={regen}" if regen else ""
                print(
                    f"    [{shot['id']}] status={status}{regen_note}\n"
                    f"         still={still}"
                )
        else:
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

    if iv.get("gate") == "human_review_images":
        while True:
            raw = input(
                "  Approve all? [y / n / shot ids to regenerate, space-separated]: "
            ).strip()
            if raw.lower() in ("y", "yes", ""):
                return {"approved": True, "regenerate_shot_ids": []}
            if raw.lower() in ("n", "no"):
                return {"approved": False, "regenerate_shot_ids": []}
            ids = raw.split()
            if ids:
                return {"approved": True, "regenerate_shot_ids": ids}
            print("  Please enter 'y', 'n', or one or more shot ids.")

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
    static_only: bool = True,
    script_fixture: str = "",
    max_levels: int = 0,
    target_minutes: float = 9.0,
    output_height: int = 0,
    voice_name: str = "",
    paid_voice: bool = False,
    image_provider: str = "gpt-image-2",
    image_quality: str = "low",
    include_hook: bool = False,
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
        voice_label = "ElevenLabs" if paid_voice else "edge-TTS (free)"
        image_label = (
            "fal FLUX.1 [schnell]"
            if image_provider == "fal"
            else f"OpenAI {image_provider} ({image_quality})"
        )
        print(f"Mode: REAL — {image_label} stills + {voice_label}")
        if not static_only:
            print("Motion enabled: Seedance video calls cost ~$1.20 per shot.")
        llm = OpenAILLMAdapter()
        image_gen = (
            OpenAIImageGenAdapter(model=image_provider, quality=image_quality)
            if image_provider != "fal"
            else FalImageGenAdapter()
        )
        video_gen = FalVideoGenAdapter()
        voice = (
            ElevenLabsVoiceAdapter()
            if paid_voice
            else (
                EdgeTTSVoiceAdapter(voice_name)
                if voice_name
                else EdgeTTSVoiceAdapter()
            )
        )

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
    initial: dict = {"topic": topic, "static_only": static_only}
    if max_shots is not None:
        initial["max_shots"] = max_shots
    if script_fixture:
        initial["script_fixture_path"] = script_fixture
    if max_levels:
        initial["max_levels"] = max_levels
    if target_minutes > 0:
        initial["target_minutes"] = target_minutes
    initial["include_hook"] = include_hook
    if output_height:
        initial["output_height"] = output_height
    result = await graph.ainvoke(initial, config)

    # Interrupt loop — handles all human-review gates.
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
    cost_log = result.get("cost_log", [])
    total_cost = sum(
        entry.get("amount_usd", 0.0) if isinstance(entry, dict) else entry.amount_usd
        for entry in cost_log
    )
    print()
    print("=" * 64)
    print("  Pipeline complete!")
    print(f"  Final video:  {result.get('final_video_path', 'N/A')}")
    print(f"  Published at: {result.get('last_published_at', 'N/A')}")
    print(f"  Total cost:   ${total_cost:.4f} ({len(cost_log)} billed calls)")
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
            "Limit the pipeline to the first N shots. Useful for cheap "
            "smoke tests — one still is about $0.01."
        ),
    )
    parser.add_argument(
        "--allow-motion",
        action="store_true",
        help=(
            "Allow shots tagged 'motion' to be animated with Seedance "
            "(~$1.20 per shot). Off by default: this format is a still "
            "slideshow, so every shot renders as static_pan."
        ),
    )
    parser.add_argument(
        "--script-fixture",
        metavar="PATH",
        default="",
        help=(
            "Use a reviewed script fixture JSON instead of generating the "
            "script with the LLM. Auto-detected for the demo topic."
        ),
    )
    parser.add_argument(
        "--levels",
        type=int,
        default=0,
        metavar="N",
        dest="max_levels",
        help=(
            "Render only the first N levels of the fixture. Use this to "
            "preview the look before committing to a full-length render."
        ),
    )
    parser.add_argument(
        "--resolution",
        type=int,
        default=0,
        choices=[720, 1080, 1440, 2160],
        metavar="HEIGHT",
        dest="output_height",
        help="Output frame height at 16:9 (default 2160, i.e. 4K).",
    )
    parser.add_argument(
        "--minutes",
        type=float,
        default=11.0,
        metavar="N",
        dest="target_minutes",
        help=(
            "Target spoken runtime in minutes (default 11, which measures "
            "out at roughly 10). Treated as a hard word ceiling when the "
            "script is written, so the full arc still lands inside it. "
            "Ignored when --script-fixture supplies a pre-written script."
        ),
    )
    parser.add_argument(
        "--voice",
        default="",
        metavar="NAME",
        dest="voice_name",
        help="edge-tts voice name (default en-US-ChristopherNeural).",
    )
    parser.add_argument(
        "--elevenlabs",
        action="store_true",
        dest="paid_voice",
        help=(
            "Narrate with ElevenLabs instead of free edge-tts "
            "(~$0.10 per 1,000 characters)."
        ),
    )
    parser.add_argument(
        "--image-provider",
        default="gpt-image-2",
        choices=[
            "fal",
            "gpt-image-2",
            "gpt-image-1.5",
            "gpt-image-1",
            "gpt-image-1-mini",
        ],
        dest="image_provider",
        help=(
            "Stills provider. Default 'gpt-image-2' (~$0.0055/image at low "
            "quality, requires OPENAI_API_KEY): the only option measured to "
            "render in-scene text reliably. 'fal' is FLUX.1 [schnell] "
            "(~$0.003/image) and cannot spell. See --image-quality."
        ),
    )
    parser.add_argument(
        "--image-quality",
        default="low",
        choices=["low", "medium", "high"],
        dest="image_quality",
        help=(
            "Quality tier for an OpenAI --image-provider (ignored for fal). "
            "Default 'low' (~$0.0055/image) is the production default: most "
            "of what medium (~$0.042, 7.6x the cost) used to buy turned out "
            "to be storyboard-prompt fixes, not rendering fidelity. 'high' "
            "is not recommended at any budget — it drifts off the locked "
            "character design."
        ),
    )
    parser.add_argument(
        "--include-hook",
        action="store_true",
        dest="include_hook",
        help=(
            "Speak the fixture/LLM script's cold-open hook line before "
            "Level One's title card (default: off — start directly on "
            "Level One)."
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
            static_only=not _args.allow_motion,
            script_fixture=_args.script_fixture,
            max_levels=_args.max_levels,
            target_minutes=_args.target_minutes,
            output_height=_args.output_height,
            voice_name=_args.voice_name,
            paid_voice=_args.paid_voice,
            image_provider=_args.image_provider,
            image_quality=_args.image_quality,
            include_hook=_args.include_hook,
        )
    )
