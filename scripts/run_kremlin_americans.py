"""One-off production run for the Kremlin-Americans 10-minute video."""

from __future__ import annotations

import asyncio
import importlib.util
import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")
os.environ.setdefault("ADAPTER_CACHE", "1")

from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command

from adapters.image_gen.fal import FalImageGenAdapter
from adapters.llm.base import (
    LLMAdapter,
    QualityCheckResult,
    ScriptResult,
    ShotBreakdownResult,
    VisualBeatsResult,
)
from adapters.llm.mock import MockLLMAdapter
from adapters.video_gen.fal import FalVideoGenAdapter
from adapters.voice.edge import EdgeTTSVoiceAdapter
from graph.graph import build_graph

TOPIC = "What the Kremlin Really Thinks About Americans"
FIXTURE = str(ROOT / "fixtures" / "kremlin_americans.json")
STORYBOARD = ROOT / "fixtures" / "kremlin_americans_storyboard.py"


def _load_scenes() -> list[tuple[str, str]]:
    spec = importlib.util.spec_from_file_location("kremlin_storyboard", STORYBOARD)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return list(module.SCENES)


class FixtureStoryboardLLM(LLMAdapter):
    """Uses the Grok-authored scene list; quality checks auto-pass (no paid LLM)."""

    def __init__(self, scenes: list[tuple[str, str]]) -> None:
        self._scenes = scenes
        self._mock = MockLLMAdapter()

    async def write_script(self, topic, brief, include_hook=True, target_minutes=0.0):
        return ScriptResult(beats=[], cost_usd=0.0)

    async def breakdown_shots(self, script, character_descriptor):
        return await self._mock.breakdown_shots(script, character_descriptor)

    async def visualize_beats(self, beats: list[str], topic: str = "") -> VisualBeatsResult:
        if len(beats) != len(self._scenes):
            raise ValueError(
                f"Storyboard has {len(self._scenes)} scenes, got {len(beats)} chunks."
            )
        descriptions = [d for _, d in self._scenes]
        shot_types = [s for s, _ in self._scenes]
        return VisualBeatsResult(
            descriptions=descriptions, shot_types=shot_types, cost_usd=0.0
        )

    async def quality_check(
        self,
        shot_id: str,
        clip_url: str,
        still_url: str,
        style_descriptor: str,
        sheet_image_urls: list[str],
    ) -> QualityCheckResult:
        return QualityCheckResult(passed=True, cost_usd=0.0)


def _gate(result: dict) -> dict:
    iv = result["__interrupt__"][0]
    return iv.value if hasattr(iv, "value") else iv


async def main() -> None:
    scenes = _load_scenes()
    print(f"Topic: {TOPIC}", flush=True)
    print(f"Fixture: {FIXTURE}", flush=True)
    print(f"Grok storyboard scenes: {len(scenes)}", flush=True)
    print("Adapters: fal FLUX schnell stills + Edge TTS + Grok storyboard", flush=True)
    print("(OpenAI, Anthropic, and ElevenLabs free-tier are unavailable.)", flush=True)

    graph = build_graph(
        llm=FixtureStoryboardLLM(scenes),
        image_gen=FalImageGenAdapter(),
        video_gen=FalVideoGenAdapter(),
        voice=EdgeTTSVoiceAdapter(),
        checkpointer=MemorySaver(),
    )
    config = {"configurable": {"thread_id": "kremlin-americans-10m"}}
    initial = {
        "topic": TOPIC,
        "static_only": True,
        "script_fixture_path": FIXTURE,
        "include_hook": True,
        "target_minutes": 10.0,
    }

    result = await graph.ainvoke(initial, config)
    while result.get("__interrupt__"):
        iv = _gate(result)
        gate = iv.get("gate")
        print(f"\n=== interrupt: {gate} — approving ===", flush=True)
        if gate == "human_review_script":
            shots = iv.get("shot_list") or []
            print(f"  shots queued: {len(shots)}", flush=True)
            payload: dict = {"approved": True, "edits": []}
        elif gate == "human_review_images":
            stills = [
                s for s in (iv.get("shot_list") or []) if not s.get("is_title_card")
            ]
            print(f"  stills to review: {len(stills)} (approving all)", flush=True)
            payload = {"approved": True, "regenerate_shot_ids": []}
        else:
            print(f"  final_video: {iv.get('final_video_path')}", flush=True)
            payload = {"approved": True, "edits": []}
        result = await graph.ainvoke(Command(resume=payload), config)

    cost_log = result.get("cost_log", [])
    total = sum(
        e.get("amount_usd", 0.0) if isinstance(e, dict) else e.amount_usd
        for e in cost_log
    )
    print("\n" + "=" * 64, flush=True)
    print("DONE", flush=True)
    print(f"Final video: {result.get('final_video_path')}", flush=True)
    print(f"Total cost: ${total:.4f} ({len(cost_log)} billed calls)", flush=True)
    print("=" * 64, flush=True)


if __name__ == "__main__":
    asyncio.run(main())
