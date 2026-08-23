"""
Generic runner for fixture-driven custom YouTube cuts.

One command per video, everything else is data:

    .venv/bin/python scripts/run_custom_video.py fixtures/video_specs/<slug>.json
    .venv/bin/python scripts/run_custom_video.py fixtures/video_specs/<slug>.json --force

A video spec is a small JSON file:

    {
      "topic":         "What X Really Thought About Y",
      "fixture":       "fixtures/x_y.json",
      "stills_module": "fixtures/x_y_stills.py",
      "still_prefix":  "x_y_v1_",
      "stills_dir":    "assets/grok_x_y_v1",
      "thread_id":     "x-y-v1",
      "voice":         "chatterbox",        // or "kokoro"
      "narration_wpm": 175,
      "voice_ref":     "assets/voice_refs/narrator.wav"   // optional
    }

The stills module must export ``STILLS`` (list of (shot_type, who, scene))
and ``prompt_for(who, scene)``; run ``scripts/lint_storyboard.py <spec>``
before generating images. Stills land in Cursor's asset folder as
``<still_prefix><NNN>.png`` and are cover-cropped to 16:9 on ingest.

This replaces the per-video ``run_*_americans.py`` scripts so a new title
needs three data files (fixture, stills module, spec) and zero new code.
"""

from __future__ import annotations

import asyncio
import importlib.util
import json
import os
import re
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
load_dotenv(ROOT / ".env", override=True)
os.environ.setdefault("ADAPTER_CACHE", "1")

# The spec must be read and pacing exported before graph.script_fixture
# is imported (NARRATION_WPM is still bound at import for shot duration math;
# chunk windows are read at call time from CHUNK_*_SECONDS).
if len(sys.argv) < 2:
    print("usage: run_custom_video.py <spec.json> [--force]", file=sys.stderr)
    sys.exit(2)
SPEC = json.loads((ROOT / sys.argv[1]).read_text(encoding="utf-8"))
_FORCE_ASSEMBLE = "--force" in sys.argv
from channel.pacing import apply_spec_pacing  # noqa: E402

apply_spec_pacing(SPEC)
if SPEC.get("voice_ref"):
    os.environ.setdefault("CHATTERBOX_VOICE_REF", str(ROOT / SPEC["voice_ref"]))
if SPEC.get("chatterbox_breath") is not None:
    os.environ.setdefault("CHATTERBOX_BREATH", str(SPEC["chatterbox_breath"]))
if SPEC.get("chatterbox_temperature") is not None:
    os.environ.setdefault("CHATTERBOX_TEMPERATURE", str(SPEC["chatterbox_temperature"]))
if SPEC.get("kokoro_voice"):
    os.environ["KOKORO_VOICE"] = str(SPEC["kokoro_voice"])
if SPEC.get("kokoro_speed") is not None:
    os.environ["KOKORO_SPEED"] = str(SPEC["kokoro_speed"])
if SPEC.get("kokoro_sentence_pause") is not None:
    os.environ["KOKORO_SENTENCE_PAUSE"] = str(SPEC["kokoro_sentence_pause"])
if SPEC.get("kokoro_clause_pause") is not None:
    os.environ["KOKORO_CLAUSE_PAUSE"] = str(SPEC["kokoro_clause_pause"])
if SPEC.get("kokoro_pack_words") is not None:
    os.environ["KOKORO_PACK_WORDS"] = str(SPEC["kokoro_pack_words"])
if SPEC.get("kokoro_scene_pause") is not None:
    os.environ["KOKORO_SCENE_PAUSE"] = str(SPEC["kokoro_scene_pause"])

from langgraph.checkpoint.memory import MemorySaver  # noqa: E402
from langgraph.types import Command  # noqa: E402

from adapters.image_gen.base import (  # noqa: E402
    DerivedStillResult,
    ImageGenAdapter,
    ReferenceSheetResult,
)
from adapters.llm.base import (  # noqa: E402
    LLMAdapter,
    QualityCheckResult,
    ScriptResult,
    VisualBeatsResult,
)
from adapters.llm.mock import MockLLMAdapter  # noqa: E402
from adapters.video_gen.fal import FalVideoGenAdapter  # noqa: E402
from graph.assets import save_asset  # noqa: E402
from graph.graph import build_graph  # noqa: E402
from graph.script_fixture import (  # noqa: E402
    fixture_to_beats,
    is_title_beat,
    load_fixture,
    split_beat_into_chunks,
    title_card_narration,
)
from graph.style import STYLE_DESCRIPTOR  # noqa: E402

TOPIC = SPEC["topic"]
FIXTURE = ROOT / SPEC["fixture"]
STILLS_DIR = ROOT / SPEC["stills_dir"]
STILL_PREFIX = SPEC["still_prefix"]
CURSOR_ASSETS = Path.home() / ".cursor" / "projects" / (
    str(ROOT).strip("/").replace("/", "-")
) / "assets"
_STILL_TAG = re.compile(r"GROKSTILL:(\d{3})")


def make_voice_adapter():
    kind = SPEC.get("voice", "chatterbox")
    if kind == "chatterbox":
        from adapters.voice.chatterbox import ChatterboxVoiceAdapter

        return ChatterboxVoiceAdapter()
    if kind == "kokoro":
        from adapters.voice.kokoro import KokoroVoiceAdapter

        return KokoroVoiceAdapter()
    raise ValueError(f"Unknown voice in spec: {kind!r}")


from scripts._media import cover_crop  # noqa: E402


class PrebuiltGrokStillAdapter(ImageGenAdapter):
    """Copy tagged pre-generated frames into the asset store. No model call."""

    def __init__(self, directory: Path) -> None:
        self._dir = directory

    async def generate_reference_sheet(
        self, character_description: str
    ) -> ReferenceSheetResult:
        hero = self._dir / f"{STILL_PREFIX}000.png"
        url = save_asset(f"refs/{STILL_PREFIX}hero.png", hero.read_bytes())
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
            raise RuntimeError(f"Missing still: {src}")
        url = save_asset(f"stills/{STILL_PREFIX}{still_id}.png", src.read_bytes())
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


def _stills_module():
    spec = importlib.util.spec_from_file_location(
        "video_stills", ROOT / SPEC["stills_module"]
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _chunk_tags() -> tuple[list[str], list[str], list[str], str]:
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
        raise ValueError(
            f"Storyboard has {len(scenes)} scenes, script has {len(chunks)} chunks. "
            "Run scripts/lint_storyboard.py first."
        )
    tags = [f"{i:03d}" for i in range(len(chunks))]
    return tags, scenes, shot_types, " ".join(s for s in spoken if s)


def gather_stills() -> list[Path]:
    """Cover-crop generated frames to 16:9 into STILLS_DIR."""
    n = len(_stills_module().STILLS)
    STILLS_DIR.mkdir(parents=True, exist_ok=True)
    missing: list[Path] = []
    for i in range(n):
        name = f"{STILL_PREFIX}{i:03d}.png"
        dest = STILLS_DIR / name
        src = CURSOR_ASSETS / name
        if src.is_file() and src.stat().st_size > 0:
            cover_crop(src, dest, 16, 9)
            continue
        if dest.is_file() and dest.stat().st_size > 0:
            continue
        missing.append(dest)
    return missing


def _gate(result: dict) -> dict:
    iv = result["__interrupt__"][0]
    return iv.value if hasattr(iv, "value") else iv


async def main() -> None:
    from channel.cadence import (
        CadenceError,
        assert_cadence,
        record_assemble,
        slug_from_spec,
    )

    slug = slug_from_spec(SPEC)
    try:
        assert_cadence(slug, force=_FORCE_ASSEMBLE)
    except CadenceError as exc:
        print(exc, file=sys.stderr)
        sys.exit(2)
    if SPEC.get("engine") == "channel":
        from channel.originality import OriginalityError, assert_originality

        try:
            report = assert_originality(slug, force=_FORCE_ASSEMBLE)
            print(
                f"Originality: {report.originality_score} "
                f"(peak similarity {report.mass_production_similarity})",
                flush=True,
            )
        except OriginalityError as exc:
            print(exc, file=sys.stderr)
            sys.exit(2)

    tags, scenes, shot_types, spoken = _chunk_tags()
    print(f"Topic: {TOPIC}", flush=True)
    print(f"Fixture: {FIXTURE}", flush=True)
    print(f"Spoken characters: {len(spoken)}", flush=True)
    print(f"Narration WPM: {os.environ.get('NARRATION_WPM')}", flush=True)
    print(f"Voice: {SPEC.get('voice', 'chatterbox')} (local, $0)", flush=True)
    print(f"Unique stills: {len(tags)} (one per chunk)", flush=True)

    missing = gather_stills()
    if missing:
        print(f"Missing {len(missing)} stills, e.g. {missing[0].name}", flush=True)
        sys.exit(2)

    graph = build_graph(
        llm=TaggedStoryboardLLM(tags, scenes, shot_types),
        image_gen=PrebuiltGrokStillAdapter(STILLS_DIR),
        video_gen=FalVideoGenAdapter(),
        voice=make_voice_adapter(),
        checkpointer=MemorySaver(),
    )
    config = {"configurable": {"thread_id": SPEC["thread_id"]}}
    burn_captions = SPEC.get("burn_captions")
    if burn_captions is None:
        burn_captions = SPEC.get("engine") == "channel"
    print(f"Captions: {'on' if burn_captions else 'off'}", flush=True)
    initial = {
        "topic": TOPIC,
        "static_only": True,
        "script_fixture_path": str(FIXTURE),
        "include_hook": True,
        "target_minutes": 23.0,
        "burn_captions": bool(burn_captions),
    }

    result = await graph.ainvoke(initial, config)
    while result.get("__interrupt__"):
        iv = _gate(result)
        gate = iv.get("gate")
        print(f"\n=== interrupt: {gate} — approving ===", flush=True)
        if gate == "human_review_script":
            print(f"  shots queued: {len(iv.get('shot_list') or [])}", flush=True)
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
    record_assemble(slug, kind="long")
    try:
        from channel.youtube import load_assemble_manifest, write_pack

        assemble = load_assemble_manifest(SPEC)
        if assemble is None and result.get("final_video_path"):
            manifest = Path(
                str(result["final_video_path"]).removeprefix("file://")
            ).with_suffix(".json")
            if manifest.is_file():
                assemble = json.loads(manifest.read_text(encoding="utf-8"))
        pack = write_pack(SPEC, assemble=assemble)
        print(f"YouTube description: {pack['description']}", flush=True)
        print(f"YouTube tags: {pack['tags']}", flush=True)
        from channel.thumbnail import render_thumbnail_jpeg
        from channel.youtube import find_thumbnail_still, youtube_dir, youtube_stem

        slug = Path(SPEC.get("fixture") or "").stem
        still = find_thumbnail_still(slug)
        if still:
            dest = youtube_dir() / f"{youtube_stem(slug)}_thumbnail_1280x720.jpg"
            text = str((SPEC.get("youtube") or {}).get("thumbnail_text") or "")
            print(
                f"YouTube thumbnail: {render_thumbnail_jpeg(still, dest, text)}",
                flush=True,
            )
    except Exception as exc:  # noqa: BLE001 — pack is convenience, never fail the cut
        print(f"YouTube pack skipped: {exc}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
