"""Cloud / fresh-clone readiness. Never print secret values."""

from __future__ import annotations

import importlib
import os
import shutil
import sys
from pathlib import Path

from channel.engine import (
    FORBIDDEN_FALLBACKS,
    MODEL_LOCK,
    PROMPT_MODULES,
    VIDEO_ENGINE_VERSION,
)
from channel.modes import ChannelMode
from channel.paths import ROOT

REQUIRED_FILES = (
    "AGENTS.md",
    "docs/custom-videos.md",
    "docs/behind-the-business.md",
    "docs/how-they-took-over.md",
    "docs/video-engine/README.md",
    "docs/video-engine/CLOUD_AGENT_START_PROMPT.md",
    "docs/channels/what-they-really-think.md",
    "docs/channels/how-they-really-make-money.md",
    "docs/channels/how-they-took-over.md",
    ".cursor/rules/custom-videos.mdc",
    ".cursor/rules/video-engine.mdc",
    ".cursor/rules/channel-routing.mdc",
    ".cursor/rules/cloud-generation.mdc",
    ".env.example",
    "channel/config.py",
    "channel/engine.py",
    "channel/generate.py",
    "channel/agent_prompts.py",
    "channel/business_prompts.py",
    "channel/takeover_prompts.py",
)

REQUIRED_ENV_NAMES = (
    # Documentary path does not need these. Graph/Phase-2 adapters do.
    "OPENAI_API_KEY",
    "ANTHROPIC_API_KEY",
    "FAL_KEY",
    "ELEVENLABS_API_KEY",
    "LANGCHAIN_API_KEY",
)


def check_readiness(*, strict: bool = False) -> dict:
    errors: list[str] = []
    warnings: list[str] = []
    for rel in REQUIRED_FILES:
        if not (ROOT / rel).is_file():
            errors.append(f"missing {rel}")
    for mode, module in PROMPT_MODULES.items():
        try:
            mod = importlib.import_module(module)
        except Exception as exc:
            errors.append(f"cannot import {module}: {exc}")
            continue
        for name in ("RESEARCHER", "STORY_ARCHITECT", "NARRATION_WRITER", "SCENE_BREAKDOWN"):
            if not getattr(mod, name, None):
                errors.append(f"{module} missing {name}")
    if ChannelMode.how_they_took_over not in PROMPT_MODULES:
        errors.append("how_they_took_over prompt module missing")
    if "cursor_grok_GenerateImage" not in MODEL_LOCK["image"]:
        errors.append("image model lock drifted off Cursor GenerateImage")
    if MODEL_LOCK["tts"] != "kokoro":
        errors.append("tts model lock drifted off kokoro")
    example = ROOT / ".env.example"
    if example.is_file():
        text = example.read_text(encoding="utf-8")
        for name in REQUIRED_ENV_NAMES:
            if name not in text:
                warnings.append(f".env.example does not name {name}")
    artifacts = ROOT / "artifacts"
    try:
        artifacts.mkdir(parents=True, exist_ok=True)
        probe = artifacts / ".write_probe"
        probe.write_text("ok\n", encoding="utf-8")
        probe.unlink(missing_ok=True)
    except OSError as exc:
        errors.append(f"artifacts/ not writable: {exc}")
    if not shutil.which("ffmpeg"):
        msg = "ffmpeg not on PATH (needed to assemble; install before render)"
        (errors if strict else warnings).append(msg)
    if sys.version_info < (3, 13):
        warnings.append(f"Python {sys.version.split()[0]} < 3.13")
    for forbidden in FORBIDDEN_FALLBACKS[:4]:
        if os.environ.get("CHANNEL_FORCE_" + forbidden.upper().replace(" ", "_")):
            errors.append(f"forbidden fallback override set for {forbidden}")
    return {
        "ok": not errors,
        "engine_version": VIDEO_ENGINE_VERSION,
        "errors": errors,
        "warnings": warnings,
        "python": sys.version.split()[0],
        "ffmpeg": shutil.which("ffmpeg") or "",
    }


def print_readiness(report: dict) -> int:
    print(f"engine_version: {report['engine_version']}")
    print(f"python: {report['python']}")
    print(f"ffmpeg: {report['ffmpeg'] or 'MISSING'}")
    for warn in report["warnings"]:
        print(f"warning: {warn}")
    for err in report["errors"]:
        print(f"error: {err}")
    print("ok" if report["ok"] else "not ready")
    return 0 if report["ok"] else 1
