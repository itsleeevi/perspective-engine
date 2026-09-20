"""Lyria 3 background music for documentary jobs.

Named engine music path: Lyria 3 Clip (`lyria-3-clip-preview`) for looping
30-second instrumental beds. `lyria-3.5` is the full-song option.
Call ``python -m channel music <JOB_ID>`` after QA. Assemble mixes the bed
quietly under narration when ``audio/music.*`` exists. Never fall back to
Suno / Udio / ElevenLabs music. Does not run on ``--resume``.
"""

from __future__ import annotations

import base64
import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

import httpx

from channel.engine import GEMINI_MUSIC_LOCK
from channel.gemini_tts import gemini_api_key
from channel.io import load_project
from channel.job import (
    ensure_job_tree,
    load_manifest,
    project_path,
    write_manifest,
    write_operator_md,
    write_report,
)
from channel.modes import ChannelMode, parse_mode

LYRIA_CLIP_MODEL = GEMINI_MUSIC_LOCK["model"]
LYRIA_FULL_MODEL = GEMINI_MUSIC_LOCK["full_model"]
LYRIA_CLIP_PUBLIC_NAME = GEMINI_MUSIC_LOCK["public_name"]
LYRIA_FULL_PUBLIC_NAME = "Lyria 3.5"
LYRIA_MIX_VOLUME = float(GEMINI_MUSIC_LOCK["mix_volume"])
LYRIA_CLIP_SECONDS = int(GEMINI_MUSIC_LOCK["clip_seconds"])
LYRIA_GENERATE_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

LYRIA_CLIP_ALIASES = frozenset(
    {
        "lyria-3-clip-preview",
        "lyria-3-clip",
        "lyria-3",
        "lyria3",
        "lyra-3",
        "lyra3",
        "clip",
    }
)
LYRIA_FULL_ALIASES = frozenset(
    {
        "lyria-3.5",
        "lyria-3-pro-preview",
        "lyria-3-pro",
        "lyria-3.5-preview",
        "pro",
        "full",
    }
)

_MUSIC_STEMS = ("music", "lyria", "bgm")
_MUSIC_SUFFIXES = (".mp3", ".wav", ".m4a", ".aac", ".ogg")
_TIMEOUT = 600.0
_MAX_RETRIES = 6
_RETRY_BASE_SECONDS = 2.0
_RETRY_MAX_SECONDS = 60.0
_INSTRUMENTAL_RULE = (
    "Instrumental only, no vocals, no lyrics, no choir, no hummed melody "
    "that could fight a spoken narrator."
)

GenerateFn = Callable[..., "LyriaMusicResult"]


class GeminiMusicError(RuntimeError):
    """Lyria 3 / Gemini music generation failed. Do not swap providers."""


@dataclass
class LyriaMusicResult:
    """One generated bed plus any lyrics/structure text the model returned."""

    data: bytes
    mime: str = "audio/mpeg"
    text: str = ""
    usage: dict[str, Any] = field(default_factory=dict)
    model: str = ""


def normalize_lyria_model(model: str = "", *, full: bool = False) -> str:
    raw = (model or "").strip().lower()
    if full and not raw:
        return LYRIA_FULL_MODEL
    if not raw or raw in LYRIA_CLIP_ALIASES:
        return LYRIA_CLIP_MODEL
    if raw in LYRIA_FULL_ALIASES:
        return LYRIA_FULL_MODEL
    return (model or LYRIA_CLIP_MODEL).strip()


def public_name_for(model: str) -> str:
    if normalize_lyria_model(model) == LYRIA_FULL_MODEL:
        return LYRIA_FULL_PUBLIC_NAME
    return LYRIA_CLIP_PUBLIC_NAME


def suffix_for_mime(mime: str) -> str:
    text = (mime or "").lower()
    if "wav" in text:
        return ".wav"
    if "mp4" in text or "m4a" in text or "aac" in text:
        return ".m4a"
    return ".mp3"


def _channel_bed(mode: ChannelMode, *, full: bool) -> str:
    length = (
        "about two minutes, designed to loop quietly"
        if full
        else f"a seamless looping {LYRIA_CLIP_SECONDS}-second clip"
    )
    beds = {
        ChannelMode.what_they_really_think: (
            "Sparse muted piano and low strings. Historical documentary "
            f"underscore. Slow, restrained, around 70 BPM. {length}."
        ),
        ChannelMode.behind_the_business: (
            "Clean modern keys, light bass, and a quiet pulse. Curious "
            f"business documentary bed, not a hype trailer. Around 90 BPM. {length}."
        ),
        ChannelMode.how_they_took_over: (
            "Taut low synth and restrained percussion. Energetic strategic "
            f"documentary bed that still sits under a narrator. Around 100 BPM. {length}."
        ),
        ChannelMode.wealth_pov: (
            "Warm acoustic guitar and soft pads. Calm second-person life "
            f"film underscore, unhurried, around 72 BPM. {length}."
        ),
    }
    return beds[mode]


def music_prompt_for(
    mode: ChannelMode | str,
    title: str = "",
    *,
    extra: str = "",
    full: bool = False,
) -> str:
    """Instrumental documentary bed. Always forbids vocals."""
    parsed = parse_mode(mode)
    bits = [
        _INSTRUMENTAL_RULE,
        "Background music only. Sit under a clear spoken voiceover. Do not peak.",
        _channel_bed(parsed, full=full),
        "No theme song, no pop chorus, no trap hats, no sudden drops.",
    ]
    headline = (title or "").strip()
    if headline:
        bits.append(
            f"Mood inspired by the documentary title {headline!r}, without "
            "quoting it as sung lyrics."
        )
    note = (extra or "").strip()
    if note:
        bits.append(note)
    return " ".join(bits)


def matching_music(job: Path) -> Path | None:
    """Return the job's background-music file when present."""
    folders = [job / "audio", job / "drop"]
    names: list[str] = []
    for stem in _MUSIC_STEMS:
        for suffix in _MUSIC_SUFFIXES:
            names.append(f"{stem}{suffix}")
    for folder in folders:
        if not folder.is_dir():
            continue
        for name in names:
            candidate = folder / name
            if candidate.is_file() and candidate.stat().st_size > 0:
                return candidate
    return None


def music_mix_volume(job: Path, default: float = LYRIA_MIX_VOLUME) -> float:
    ledger = job / "audio" / "music_ledger.json"
    if not ledger.is_file():
        return default
    try:
        data = json.loads(ledger.read_text(encoding="utf-8"))
        value = float(data.get("mix_volume", default))
    except (OSError, TypeError, ValueError, json.JSONDecodeError):
        return default
    if value != value or value <= 0:
        return default
    return min(1.0, value)


def _qa_ready(dest: Path, job_id: str, artifacts_root: Path | None) -> bool:
    manifest = load_manifest(job_id, root=artifacts_root)
    if manifest.qa.get("ready_to_publish") is True:
        return True
    path = project_path(job_id, root=artifacts_root)
    if not path.is_file():
        return False
    project = load_project(path)
    if project.monetization and project.monetization.ready_to_publish:
        return True
    return False


def _headers(api_key: str) -> dict[str, str]:
    return {
        "Content-Type": "application/json",
        "x-goog-api-key": api_key,
    }


def _retry_sleep(attempt: int) -> float:
    return min(_RETRY_MAX_SECONDS, _RETRY_BASE_SECONDS * (2 ** attempt))


def _inline_audio(payload: dict[str, Any]) -> tuple[bytes, str, str]:
    texts: list[str] = []
    audio: bytes | None = None
    mime = "audio/mpeg"

    def take_part(part: dict[str, Any]) -> None:
        nonlocal audio, mime
        text = part.get("text")
        if isinstance(text, str) and text.strip():
            texts.append(text.strip())
        inline = part.get("inlineData") or part.get("inline_data")
        if isinstance(inline, dict) and inline.get("data"):
            audio = base64.b64decode(inline["data"])
            mime = str(inline.get("mimeType") or inline.get("mime_type") or mime)
        if str(part.get("type") or "") == "audio" and part.get("data"):
            audio = base64.b64decode(part["data"])
            mime = str(part.get("mime_type") or part.get("mimeType") or mime)

    try:
        for cand in payload.get("candidates") or []:
            content = cand.get("content") or {}
            for part in content.get("parts") or []:
                if isinstance(part, dict):
                    take_part(part)
        for blob in payload.get("output") or payload.get("outputs") or []:
            if isinstance(blob, dict):
                take_part(blob)
        for key in ("output_audio", "outputAudio"):
            blob = payload.get(key)
            if isinstance(blob, dict):
                take_part(blob)
        for step in payload.get("steps") or []:
            if not isinstance(step, dict):
                continue
            for part in step.get("content") or []:
                if isinstance(part, dict):
                    take_part(part)
        if not audio:
            raise KeyError("inlineData")
        return audio, mime, "\n".join(texts)
    except (KeyError, IndexError, TypeError, ValueError) as exc:
        err = payload.get("error") or payload.get("promptFeedback") or payload
        raise GeminiMusicError(f"Lyria 3 response had no audio: {err!r}") from exc


def generate_music(
    prompt: str,
    *,
    api_key: str,
    model: str = LYRIA_CLIP_MODEL,
    client: httpx.Client | None = None,
    timeout: float = _TIMEOUT,
    retries: int = _MAX_RETRIES,
) -> LyriaMusicResult:
    if not api_key:
        raise GeminiMusicError(
            "GEMINI_API_KEY (or GOOGLE_API_KEY) is missing. "
            "Assemble still muxes narration only. "
            "Do not fall back to Suno, Udio, or ElevenLabs music."
        )
    locked = normalize_lyria_model(model)
    body: dict[str, Any] = {
        "contents": [{"parts": [{"text": prompt}]}],
    }
    if locked == LYRIA_FULL_MODEL:
        body["generationConfig"] = {
            "responseModalities": ["AUDIO", "TEXT"],
        }
    url = LYRIA_GENERATE_URL.format(model=locked)
    own_client = client is None
    http = client or httpx.Client(timeout=timeout)
    last_error = ""
    try:
        for attempt in range(retries):
            response = http.post(url, headers=_headers(api_key), json=body)
            if response.status_code in {429, 503, 500} and attempt + 1 < retries:
                last_error = response.text[:800]
                time.sleep(_retry_sleep(attempt))
                continue
            if response.status_code >= 400:
                raise GeminiMusicError(
                    f"Lyria 3 HTTP {response.status_code}: {response.text[:800]}"
                )
            payload = response.json()
            data, mime, text = _inline_audio(payload)
            if not data:
                raise GeminiMusicError("Lyria 3 returned empty audio")
            return LyriaMusicResult(
                data=data,
                mime=mime,
                text=text,
                usage=payload.get("usageMetadata") or payload.get("usage") or {},
                model=locked,
            )
    finally:
        if own_client:
            http.close()
    raise GeminiMusicError(last_error or "Lyria 3 failed after retries")


def _mix_filter(
    volume: float,
    fade_in: float,
    fade_out: float,
    duration: float,
) -> str:
    fade_out_start = max(0.0, float(duration) - float(fade_out))
    vol = f"{float(volume):.4f}"
    return (
        f"[1:a]aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo,"
        f"apad[vo];"
        f"[2:a]aformat=sample_fmts=fltp:sample_rates=48000:channel_layouts=stereo,"
        f"volume={vol},"
        f"afade=t=in:st=0:d={float(fade_in):.2f},"
        f"afade=t=out:st={fade_out_start:.2f}:d={float(fade_out):.2f}[bg];"
        f"[vo][bg]amix=inputs=2:duration=first:dropout_transition=2[a]"
    )


def mix_narration_and_music(
    video: Path,
    voiceover: Path,
    music: Path,
    dest: Path,
    *,
    volume: float = LYRIA_MIX_VOLUME,
    fade_in: float = 2.0,
    fade_out: float = 3.0,
    duration_seconds: float | None = None,
) -> Path:
    """Loop the bed under VO, pad to the picture, keep narration louder."""
    from adapters.voice._audio import duration_seconds as probe_duration
    from graph.nodes.assemble import _run

    length = duration_seconds
    if length is None:
        try:
            length = probe_duration(video)
        except Exception:
            length = probe_duration(voiceover)
    dest.parent.mkdir(parents=True, exist_ok=True)
    _run(
        [
            "ffmpeg",
            "-y",
            "-loglevel",
            "error",
            "-i",
            str(video),
            "-i",
            str(voiceover),
            "-stream_loop",
            "-1",
            "-i",
            str(music),
            "-filter_complex",
            _mix_filter(volume, fade_in, fade_out, length),
            "-map",
            "0:v:0",
            "-map",
            "[a]",
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-ar",
            "48000",
            "-shortest",
            "-movflags",
            "+faststart",
            str(dest),
        ]
    )
    return dest


def generate_job_music(
    job_id: str,
    *,
    artifacts_root: Path | None = None,
    model: str = "",
    full: bool = False,
    prompt: str = "",
    extra: str = "",
    force: bool = False,
    dry_run: bool = False,
    mix_volume: float | None = None,
    client: httpx.Client | None = None,
    generate: GenerateFn | None = None,
    api_key: str | None = None,
) -> dict[str, Any]:
    dest = ensure_job_tree(job_id, root=artifacts_root)
    manifest = load_manifest(job_id, root=artifacts_root)
    if not force and not _qa_ready(dest, job_id, artifacts_root):
        raise GeminiMusicError(
            f"not ready_to_publish — do not call Lyria 3 for {job_id}. "
            "Run qa until originality_score >= 80 and ready_to_publish, or pass --force."
        )
    locked = normalize_lyria_model(model, full=full)
    is_full = locked == LYRIA_FULL_MODEL
    text = (prompt or "").strip() or music_prompt_for(
        manifest.channel_mode,
        manifest.title,
        extra=extra,
        full=is_full,
    )
    if _INSTRUMENTAL_RULE.lower() not in text.lower():
        text = f"{_INSTRUMENTAL_RULE} {text}".strip()
    volume = LYRIA_MIX_VOLUME if mix_volume is None else float(mix_volume)
    audio_dir = dest / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)
    existing = matching_music(dest)
    if existing is not None and not force and not dry_run:
        ledger_path = audio_dir / "music_ledger.json"
        return {
            "job_id": job_id,
            "model": locked,
            "skipped": 1,
            "generated": 0,
            "path": str(existing),
            "ledger": str(ledger_path),
            "dry_run": False,
        }

    key = api_key if api_key is not None else gemini_api_key()
    if not dry_run and generate is None and not key:
        raise GeminiMusicError(
            "GEMINI_API_KEY (or GOOGLE_API_KEY) is missing. "
            "Assemble still muxes narration only. "
            "Do not fall back to Suno, Udio, or ElevenLabs music."
        )

    prompt_path = audio_dir / "music.prompt.txt"
    prompt_path.write_text(text + "\n", encoding="utf-8")
    if dry_run:
        return {
            "job_id": job_id,
            "model": locked,
            "generated": 0,
            "skipped": 0,
            "dry_run": True,
            "prompt": text,
            "prompt_path": str(prompt_path),
        }

    synth = generate or (
        lambda p, **kwargs: generate_music(
            p, api_key=key, model=locked, client=client, **kwargs
        )
    )
    result = synth(text)
    suffix = suffix_for_mime(result.mime)
    target = audio_dir / f"music{suffix}"
    target.write_bytes(result.data)
    for leftover in audio_dir.glob("music.*"):
        if leftover == target or leftover.name.endswith(".txt"):
            continue
        if leftover.suffix.lower() in _MUSIC_SUFFIXES:
            leftover.unlink(missing_ok=True)
    ledger = {
        "model": result.model or locked,
        "public_name": public_name_for(locked),
        "lock": GEMINI_MUSIC_LOCK,
        "instrumental": True,
        "mix_volume": volume,
        "file": f"audio/{target.name}",
        "mime": result.mime,
        "bytes": target.stat().st_size,
        "prompt": text,
        "text": result.text,
        "usage": result.usage,
    }
    ledger_path = audio_dir / "music_ledger.json"
    ledger_path.write_text(json.dumps(ledger, indent=2) + "\n", encoding="utf-8")
    manifest.models["music"] = result.model or locked
    manifest.paths["music"] = str(target)
    manifest.paths["music_ledger"] = str(ledger_path)
    write_manifest(manifest, root=artifacts_root)
    write_report(manifest, root=artifacts_root)
    write_operator_md(manifest, root=artifacts_root)
    return {
        "job_id": job_id,
        "model": result.model or locked,
        "generated": 1,
        "skipped": 0,
        "path": str(target),
        "ledger": str(ledger_path),
        "prompt": text,
        "mix_volume": volume,
        "dry_run": False,
    }


__all__ = [
    "GEMINI_MUSIC_LOCK",
    "LYRIA_CLIP_MODEL",
    "LYRIA_FULL_MODEL",
    "LYRIA_MIX_VOLUME",
    "GeminiMusicError",
    "LyriaMusicResult",
    "generate_job_music",
    "generate_music",
    "matching_music",
    "mix_narration_and_music",
    "music_mix_volume",
    "music_prompt_for",
    "normalize_lyria_model",
]
