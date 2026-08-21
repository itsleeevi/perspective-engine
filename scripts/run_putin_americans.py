"""Putin-Americans v2: first-person VO, one Grok still per chunk, ElevenLabs."""

from __future__ import annotations

import asyncio
import importlib.util
import os
import re
import shutil
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env", override=True)
os.environ.setdefault("ADAPTER_CACHE", "1")

from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command

from adapters.image_gen.base import (
    DerivedStillResult,
    ImageGenAdapter,
    ReferenceSheetResult,
)
from adapters.llm.base import (
    LLMAdapter,
    QualityCheckResult,
    ScriptResult,
    VisualBeatsResult,
)
from adapters.llm.mock import MockLLMAdapter
from adapters.video_gen.fal import FalVideoGenAdapter
from adapters.voice.base import VoiceAdapter, VoiceoverResult
from adapters.voice.edge import EdgeTTSVoiceAdapter
from adapters.voice.elevenlabs import ElevenLabsVoiceAdapter
from graph.assets import save_asset
from graph.graph import build_graph
from graph.script_fixture import (
    fixture_to_beats,
    is_title_beat,
    load_fixture,
    split_beat_into_chunks,
    title_card_narration,
)
from graph.style import STYLE_DESCRIPTOR

TOPIC = "What Vladimir Putin Really Thinks About Americans"
FIXTURE = ROOT / "fixtures" / "putin_americans.json"
STILLS_DIR = ROOT / "assets" / "grok_putin_v5"
CURSOR_ASSETS = Path(
    "/home/levente/.cursor/projects/home-levente-perspective-engine/assets"
)
MAX_ELEVENLABS_CHARS = 10_000
_STILL_TAG = re.compile(r"GROKSTILL:(\d{3})")
STILL_PREFIX = "putin_v5_"
N_STILLS = 147
LIAM_VOICE_ID = "TX3LPaxmHKxFdv7VOQHJ"


class PrebuiltGrokStillAdapter(ImageGenAdapter):
    """Copy tagged Grok frames into the asset store. No image-model call."""

    def __init__(self, directory: Path) -> None:
        self._dir = directory

    async def generate_reference_sheet(
        self, character_description: str
    ) -> ReferenceSheetResult:
        hero = self._dir / f"{STILL_PREFIX}000.png"
        url = save_asset("refs/grok_putin_v5_hero.png", hero.read_bytes())
        return ReferenceSheetResult(
            image_urls=[url], style_descriptor=STYLE_DESCRIPTOR, cost_usd=0.0
        )

    async def derive_still(
        self,
        shot_prompt: str,
        sheet_image_urls: list[str],
        style_descriptor: str,
        attempt: int = 0,
    ) -> DerivedStillResult:
        match = _STILL_TAG.search(shot_prompt)
        if not match:
            raise RuntimeError(f"No GROKSTILL tag in prompt: {shot_prompt[:120]!r}")
        still_id = match.group(1)
        src = self._dir / f"{STILL_PREFIX}{still_id}.png"
        if not src.is_file():
            raise RuntimeError(f"Missing Grok still: {src}")
        url = save_asset(f"stills/grok_putin_v5_{still_id}.png", src.read_bytes())
        return DerivedStillResult(still_url=url, cost_usd=0.0)


class TaggedStoryboardLLM(LLMAdapter):
    """One GROKSTILL tag per chunk; quality checks auto-pass."""

    def __init__(
        self, tags: list[str], descriptions: list[str], shot_types: list[str]
    ) -> None:
        self._tags = tags
        self._descriptions = descriptions
        self._shot_types = shot_types
        self._mock = MockLLMAdapter()

    async def write_script(self, topic, brief, include_hook=True, target_minutes=0.0):
        return ScriptResult(beats=[], cost_usd=0.0)

    async def breakdown_shots(self, script, character_descriptor):
        return await self._mock.breakdown_shots(script, character_descriptor)

    async def visualize_beats(self, beats: list[str], topic: str = "") -> VisualBeatsResult:
        if len(beats) != len(self._tags):
            raise ValueError(
                f"Expected {len(self._tags)} chunks, visualize_beats got {len(beats)}."
            )
        descriptions = [
            f"GROKSTILL:{tag} {desc}"
            for tag, desc in zip(self._tags, self._descriptions, strict=True)
        ]
        return VisualBeatsResult(
            descriptions=descriptions,
            shot_types=list(self._shot_types),
            cost_usd=0.0,
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


class ElevenLabsPreferringVoice(VoiceAdapter):
    """ElevenLabs first; Edge only if the account still refuses the call."""

    def __init__(self) -> None:
        os.environ["ELEVENLABS_VOICE_ID"] = LIAM_VOICE_ID
        self._el = ElevenLabsVoiceAdapter()
        self._edge = EdgeTTSVoiceAdapter()

    async def synthesize(
        self,
        script_beats: list[str],
        shot_durations: list[float],
        voice_id: str = "default",
    ) -> VoiceoverResult:
        try:
            result = await self._el.synthesize(
                script_beats, shot_durations, LIAM_VOICE_ID
            )
            print("Voice: ElevenLabs Liam", flush=True)
            return result
        except Exception as exc:
            print(f"ElevenLabs failed ({exc}). Falling back to Edge TTS.", flush=True)
            return await self._edge.synthesize(script_beats, shot_durations, voice_id)


def _stills_module():
    spec = importlib.util.spec_from_file_location(
        "putin_stills", ROOT / "fixtures" / "putin_americans_stills.py"
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _chunk_tags_and_copy() -> tuple[list[str], list[str], list[str], str]:
    stills = list(_stills_module().STILLS)
    scenes = [s[2] for s in stills]
    shot_types = [s[0] for s in stills]
    data = load_fixture(str(FIXTURE))
    beats = fixture_to_beats(data, include_hook=True)
    chunks: list[str] = []
    spoken: list[str] = []
    for beat in beats:
        if is_title_beat(beat):
            spoken.append(title_card_narration(beat))
            continue
        for chunk in split_beat_into_chunks(beat):
            chunks.append(chunk)
            spoken.append(chunk.strip())
    if len(chunks) != len(scenes):
        raise ValueError(f"Storyboard has {len(scenes)} scenes, script has {len(chunks)} chunks.")
    tags = [f"{i:03d}" for i in range(len(chunks))]
    return tags, scenes, shot_types, " ".join(spoken)


def gather_stills() -> list[Path]:
    """Copy generated frames from the Cursor asset dir into STILLS_DIR."""
    STILLS_DIR.mkdir(parents=True, exist_ok=True)
    missing: list[Path] = []
    for i in range(N_STILLS):
        name = f"{STILL_PREFIX}{i:03d}.png"
        dest = STILLS_DIR / name
        if dest.is_file() and dest.stat().st_size > 0:
            continue
        src = CURSOR_ASSETS / name
        if src.is_file() and src.stat().st_size > 0:
            shutil.copy2(src, dest)
            continue
        missing.append(dest)
    return missing


def _gate(result: dict) -> dict:
    iv = result["__interrupt__"][0]
    return iv.value if hasattr(iv, "value") else iv


async def main() -> None:
    tags, copy, shot_types, spoken = _chunk_tags_and_copy()
    n_chars = len(spoken)
    print(f"Topic: {TOPIC}", flush=True)
    print(f"Fixture: {FIXTURE}", flush=True)
    print(f"Spoken characters: {n_chars} / {MAX_ELEVENLABS_CHARS} ElevenLabs cap", flush=True)
    print(f"Unique Grok stills: {len(tags)} (one per chunk)", flush=True)
    print(
        f"Character-free inserts: {sum(1 for s in _stills_module().STILLS if s[1] == 'empty')}",
        flush=True,
    )
    if n_chars > MAX_ELEVENLABS_CHARS:
        print("Spoken text exceeds the 10k credit cap. Aborting.", flush=True)
        sys.exit(2)

    missing = gather_stills()
    if missing:
        print(f"Missing {len(missing)} stills, e.g. {missing[0].name}", flush=True)
        sys.exit(2)

    graph = build_graph(
        llm=TaggedStoryboardLLM(tags, copy, shot_types),
        image_gen=PrebuiltGrokStillAdapter(STILLS_DIR),
        video_gen=FalVideoGenAdapter(),
        voice=ElevenLabsPreferringVoice(),
        checkpointer=MemorySaver(),
    )
    config = {"configurable": {"thread_id": "putin-americans-v5"}}
    initial = {
        "topic": TOPIC,
        "static_only": True,
        "script_fixture_path": str(FIXTURE),
        "include_hook": True,
        "target_minutes": 8.0,
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
    sys.path.insert(0, str(ROOT))
    asyncio.run(main())
