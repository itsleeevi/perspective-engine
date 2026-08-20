"""
Minimal FastAPI review UI for the Perspective Engine pipeline.

Replaces the terminal y/n prompts in ``cli/run.py`` with a browser page.
Runs the same graph, same adapters, same invariants; this module only
adds a web front-end around the human-review interrupt gates.

Usage:
    python -m webui.server
    # then open http://localhost:8765

Design:
    A single in-process run at a time (module-level state). The pipeline
    runs in a background asyncio task; when it hits an interrupt(), the
    task blocks on an asyncio.Queue until the browser POSTs a resume
    decision. This keeps the graph/adapters code completely untouched;
    this module only orchestrates the same ``graph.ainvoke`` /
    ``Command(resume=...)`` calls cli/run.py already makes.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

# Load .env before importing any adapter (keys must be in os.environ).
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

import asyncio

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command
from pydantic import BaseModel

from adapters.image_gen.fal import FalImageGenAdapter
from adapters.image_gen.mock import MockImageGenAdapter
from adapters.llm.anthropic import AnthropicLLMAdapter
from adapters.llm.mock import MockLLMAdapter
from adapters.video_gen.fal import FalVideoGenAdapter
from adapters.video_gen.mock import MockVideoGenAdapter
from adapters.voice.elevenlabs import ElevenLabsVoiceAdapter
from adapters.voice.mock import MockVoiceAdapter
from graph.assets import _assets_root
from graph.graph import build_graph

_STATIC_DIR = Path(__file__).parent / "static"

app = FastAPI(title="Perspective Engine: Review UI")
app.mount("/static", StaticFiles(directory=_STATIC_DIR), name="static")
app.mount("/assets", StaticFiles(directory=_assets_root()), name="assets")


# ── In-process run state (single run at a time) ───────────────────────────────


class RunState:
    def __init__(self) -> None:
        self.status: str = "idle"  # idle | running | waiting_review | done | error | aborted
        self.topic: str = ""
        self.interrupt: dict | None = None
        self.result: dict | None = None
        self.error: str | None = None
        self.resume_queue: asyncio.Queue[dict] = asyncio.Queue()
        self.task: asyncio.Task | None = None

    def reset(self, topic: str) -> None:
        self.status = "running"
        self.topic = topic
        self.interrupt = None
        self.result = None
        self.error = None
        self.resume_queue = asyncio.Queue()


state = RunState()


# ── Request / response models ─────────────────────────────────────────────────


class StartRequest(BaseModel):
    topic: str
    mock: bool = False
    static_only: bool = False
    max_shots: int | None = None
    no_cache: bool = False


class ResumeRequest(BaseModel):
    approved: bool
    edits: list[dict] = []
    regenerate_shot_ids: list[str] = []


def _still_web_path(file_url: str) -> str:
    """Map a local file:// asset URL onto the /assets static mount."""
    if not file_url:
        return ""
    if file_url.startswith("/assets/"):
        return file_url
    path = file_url.removeprefix("file://")
    root = str(_assets_root())
    if path.startswith(root):
        rel = path[len(root) :].lstrip("/")
        return f"/assets/{rel}"
    return file_url


def _serialize_shot(shot: Any) -> dict:
    still_url = shot.get("still_url", "") if isinstance(shot, dict) else shot.still_url
    return {
        "id": shot["id"] if isinstance(shot, dict) else shot.id,
        "mode": str(shot["mode"] if isinstance(shot, dict) else shot.mode),
        "status": str(shot["status"] if isinstance(shot, dict) else shot.status),
        "prompt": shot["prompt"] if isinstance(shot, dict) else shot.prompt,
        "retry_count": shot.get("retry_count", 0) if isinstance(shot, dict) else shot.retry_count,
        "manual_regen_count": (
            shot.get("manual_regen_count", 0)
            if isinstance(shot, dict)
            else shot.manual_regen_count
        ),
        "is_title_card": (
            shot.get("is_title_card", False)
            if isinstance(shot, dict)
            else shot.is_title_card
        ),
        "still_url": _still_web_path(still_url),
        "clip_url": shot.get("clip_url", "") if isinstance(shot, dict) else shot.clip_url,
        "quality_failure_reason": (
            shot.get("quality_failure_reason", "")
            if isinstance(shot, dict)
            else shot.quality_failure_reason
        ),
    }


def _serialize_interrupt(iv: dict) -> dict:
    """Normalise an interrupt payload into plain JSON for the browser."""
    out: dict = {
        "gate": iv.get("gate", "unknown"),
        "message": iv.get("message", ""),
    }
    if "script" in iv:
        out["script"] = list(iv["script"])
    if "shot_list" in iv:
        out["shot_list"] = [_serialize_shot(s) for s in iv["shot_list"]]
    if "final_video_path" in iv:
        out["final_video_path"] = iv["final_video_path"]
    if "metadata" in iv:
        meta = iv["metadata"]
        out["metadata"] = {
            "title": meta.get("title", "") if isinstance(meta, dict) else meta.title,
            "description": meta.get("description", "") if isinstance(meta, dict) else meta.description,
        }
    if "shot_summary" in iv:
        out["shot_summary"] = list(iv["shot_summary"])
    return out


# ── Pipeline runner (background task) ──────────────────────────────────────────


async def _run_pipeline(
    topic: str,
    mock: bool,
    static_only: bool,
    max_shots: int | None,
    no_cache: bool,
) -> None:
    if mock:
        os.environ["ADAPTER_CACHE"] = "0"
        llm: Any = MockLLMAdapter()
        image_gen: Any = MockImageGenAdapter()
        video_gen: Any = MockVideoGenAdapter()
        voice: Any = MockVoiceAdapter()
    else:
        os.environ["ADAPTER_CACHE"] = "0" if no_cache else os.environ.get("ADAPTER_CACHE", "1")
        llm = AnthropicLLMAdapter()
        image_gen = FalImageGenAdapter()
        video_gen = FalVideoGenAdapter()
        voice = ElevenLabsVoiceAdapter()

    checkpointer = MemorySaver()
    graph = build_graph(
        llm=llm,
        image_gen=image_gen,
        video_gen=video_gen,
        voice=voice,
        checkpointer=checkpointer,
    )
    config: dict = {"configurable": {"thread_id": f"webui-{topic!r}"}}

    try:
        initial: dict = {"topic": topic}
        if max_shots is not None:
            initial["max_shots"] = max_shots
        if static_only:
            initial["static_only"] = True

        result = await graph.ainvoke(initial, config)

        while result.get("__interrupt__"):
            interrupt_obj = result["__interrupt__"][0]
            iv: dict = interrupt_obj.value if hasattr(interrupt_obj, "value") else interrupt_obj

            state.interrupt = _serialize_interrupt(iv)
            state.status = "waiting_review"

            resume_payload = await state.resume_queue.get()

            state.interrupt = None
            state.status = "running"

            if not resume_payload.get("approved", False):
                state.status = "aborted"
                return

            result = await graph.ainvoke(Command(resume=resume_payload), config)

        cost_log = result.get("cost_log", [])
        total_cost = sum(
            entry.get("amount_usd", 0.0) if isinstance(entry, dict) else entry.amount_usd
            for entry in cost_log
        )
        state.result = {
            "final_video_path": result.get("final_video_path", ""),
            "last_published_at": result.get("last_published_at", ""),
            "total_cost_usd": round(total_cost, 4),
        }
        state.status = "done"
    except Exception as exc:  # noqa: BLE001 (surface any failure to the browser)
        state.error = str(exc)
        state.status = "error"


# ── API routes ─────────────────────────────────────────────────────────────────


@app.get("/")
async def index() -> FileResponse:
    return FileResponse(_STATIC_DIR / "index.html")


@app.post("/api/start")
async def start_run(req: StartRequest) -> dict:
    if state.status in ("running", "waiting_review"):
        raise HTTPException(409, "A run is already in progress.")

    state.reset(req.topic)
    state.task = asyncio.create_task(
        _run_pipeline(req.topic, req.mock, req.static_only, req.max_shots, req.no_cache)
    )
    return {"status": state.status}


@app.get("/api/state")
async def get_state() -> dict:
    return {
        "status": state.status,
        "topic": state.topic,
        "interrupt": state.interrupt,
        "result": state.result,
        "error": state.error,
    }


@app.post("/api/resume")
async def resume_run(req: ResumeRequest) -> dict:
    if state.status != "waiting_review":
        raise HTTPException(409, "No interrupt is currently awaiting review.")
    await state.resume_queue.put(req.model_dump())
    return {"status": "resuming"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8765)
