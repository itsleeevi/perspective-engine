"""Gemini 3.1 Flash TTS for documentary narration.

Named provider on new generate-path jobs. Operator ingest-audio still works
when the key is missing. Never fall back to ElevenLabs, Edge, or Kokoro.
"""

from __future__ import annotations

import base64
import json
import os
import re
import shutil
import subprocess
import time
import wave
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable

import httpx

from channel.engine import GEMINI_TTS_LOCK
from channel.job import ARTIFACTS, ensure_job_tree, load_manifest, write_manifest
from channel.modes import ChannelMode, parse_mode
from channel.paths import ROOT

GEMINI_TTS_MODEL = GEMINI_TTS_LOCK["model"]
GEMINI_TTS_VOICE = GEMINI_TTS_LOCK["voice"]
GEMINI_TTS_SAMPLE_RATE = int(GEMINI_TTS_LOCK["sample_rate"])
GEMINI_TTS_ENDPOINT = (
    f"https://generativelanguage.googleapis.com/v1beta/models/"
    f"{GEMINI_TTS_MODEL}:generateContent"
)

TARGET_WORDS = 145
MIN_WORDS = 120
MAX_WORDS = 180
MAX_CHARS = 1200
AUDIO_TAGS_DEFAULT = False

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")
_CLAUSE_SPLIT = re.compile(r"(?<=[;:])\s+")
_TAG = re.compile(r"\[[^\[\]]+\]")
_ENV_LOADED = False


class GeminiTtsError(RuntimeError):
    """Gemini TTS failed. Do not swap in another speech provider."""


@dataclass(frozen=True)
class SpokenChunk:
    index: int
    transcript: str
    word_count: int
    char_count: int
    prompt: str
    era: str = ""

    def stem(self) -> str:
        return f"{self.index:03d}"


def _load_env() -> None:
    global _ENV_LOADED
    if _ENV_LOADED:
        return
    _ENV_LOADED = True
    if os.environ.get("PYTEST_CURRENT_TEST"):
        return
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    load_dotenv(ROOT / ".env")


def gemini_api_key() -> str:
    _load_env()
    return (
        os.environ.get("GEMINI_API_KEY", "").strip()
        or os.environ.get("GOOGLE_API_KEY", "").strip()
        or os.environ.get("GOOGLE_GENAI_API_KEY", "").strip()
    )


def normalize_ws(text: str) -> str:
    return " ".join(text.split())


def spoken_words(text: str) -> list[str]:
    cleaned = _TAG.sub(" ", text)
    return [tok for tok in cleaned.split() if tok]


def spoken_word_count(text: str) -> int:
    return len(spoken_words(text))


def _sentences(script: str) -> list[str]:
    out: list[str] = []
    for para in re.split(r"\n\s*\n", script.strip()):
        para = normalize_ws(para)
        if not para:
            continue
        bits = _SENTENCE_SPLIT.split(para)
        for bit in bits:
            bit = bit.strip()
            if bit:
                out.append(bit)
    return out


def _fits(text: str) -> bool:
    return spoken_word_count(text) <= MAX_WORDS and len(text) <= MAX_CHARS


def _split_oversize(text: str) -> list[str]:
    if _fits(text):
        return [text]
    parts = [p.strip() for p in _CLAUSE_SPLIT.split(text) if p.strip()]
    if len(parts) == 1:
        parts = [p.strip() for p in re.split(r"(?<=,)\s+", text) if p.strip()]
    packed: list[str] = []
    buf: list[str] = []
    for part in parts:
        candidate = " ".join(buf + [part]).strip() if buf else part
        if buf and not _fits(candidate):
            packed.append(" ".join(buf))
            buf = [part]
            if not _fits(part):
                packed.append(part)
                buf = []
            continue
        buf.append(part)
    if buf:
        packed.append(" ".join(buf))
    return packed or [text]


def chunk_script(
    script: str,
    *,
    target_words: int = TARGET_WORDS,
    min_words: int = MIN_WORDS,
    max_words: int = MAX_WORDS,
    max_chars: int = MAX_CHARS,
) -> list[str]:
    """Split clean narration at sentence or paragraph boundaries."""
    text = script.strip()
    if not text:
        return []
    sentences = _sentences(text)
    if not sentences:
        return [normalize_ws(text)] if text else []

    chunks: list[str] = []
    buf: list[str] = []

    def buf_text() -> str:
        return " ".join(buf)

    for sent in sentences:
        pieces = _split_oversize(sent) if not _fits(sent) else [sent]
        for piece in pieces:
            candidate = f"{buf_text()} {piece}".strip() if buf else piece
            words = spoken_word_count(candidate)
            chars = len(candidate)
            if buf and (words > max_words or chars > max_chars):
                chunks.append(buf_text())
                buf = [piece]
                continue
            if buf:
                current_words = spoken_word_count(buf_text())
                if current_words >= min_words and words > target_words + 25:
                    chunks.append(buf_text())
                    buf = [piece]
                    continue
            buf.append(piece)
    if buf:
        chunks.append(buf_text())
    return chunks


def _audio_profile(mode: ChannelMode) -> tuple[str, str]:
    if mode is ChannelMode.wealth_pov:
        return (
            "Charon",
            "Warm observant storyteller. Calm confidence, curiosity, occasional "
            "dry humor. Close dry recording. American English. One original "
            "narrator — never an impression of a celebrity, never a child voice.",
        )
    return (
        "Charon",
        "Informative American English narrator. Calm, clear, measured. Close "
        "dry recording. One original documentary voice. Not a celebrity impression.",
    )


def build_tts_prompt(
    transcript: str,
    *,
    mode: ChannelMode,
    audio_tags: bool = AUDIO_TAGS_DEFAULT,
    era: str = "",
) -> str:
    name, profile = _audio_profile(mode)
    scene = era.strip() or (
        "This chunk continues the same narration. Keep the same microphone "
        "distance, accent, and recording character."
    )
    notes = (
        "Measured pace. Recite the TRANSCRIPT exactly once, in order. "
        "Do not read the headings, profile, or these notes aloud. "
        "Do not add a title, greeting, or closing."
    )
    if not audio_tags:
        notes += " Do not insert spoken audio tags or cue words."
    return (
        "Synthesize speech from the TRANSCRIPT only. Everything before it is "
        "performance direction. Recite the narrative words exactly once, in "
        "order, without an introduction or commentary.\n\n"
        f"# AUDIO PROFILE: {name}\n"
        f"{profile}\n\n"
        "## THE SCENE\n"
        f"{scene}\n\n"
        "### DIRECTOR'S NOTES\n"
        f"{notes}\n\n"
        "### SAMPLE CONTEXT\n"
        "The listener is already inside this story. Continue without a title "
        "or greeting.\n\n"
        "#### TRANSCRIPT\n"
        f"{transcript.strip()}"
    )


def chunks_for_script(
    script: str,
    *,
    mode: ChannelMode,
    audio_tags: bool = AUDIO_TAGS_DEFAULT,
) -> list[SpokenChunk]:
    out: list[SpokenChunk] = []
    for i, transcript in enumerate(chunk_script(script)):
        out.append(
            SpokenChunk(
                index=i,
                transcript=transcript,
                word_count=spoken_word_count(transcript),
                char_count=len(transcript),
                prompt=build_tts_prompt(transcript, mode=mode, audio_tags=audio_tags),
            )
        )
    return out


def transcripts_match_script(chunks: list[SpokenChunk], script: str) -> bool:
    joined = normalize_ws(" ".join(c.transcript for c in chunks))
    return joined == normalize_ws(script)


def format_tts_chunks_file(chunks: list[SpokenChunk], *, model: str, voice: str) -> str:
    lines = [
        f"# Gemini TTS chunks — {model} / {voice}",
        "# Audio tags off unless --audio-tags. Direction is outside TRANSCRIPT.",
        "",
    ]
    for chunk in chunks:
        lines.extend(
            [
                f"# CHUNK {chunk.index:03d}",
                f"# words: {chunk.word_count}",
                f"# chars: {chunk.char_count}",
                f"# era: {chunk.era or '-'}",
                "",
                chunk.prompt,
                "",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def write_pcm_wav(
    path: Path,
    pcm: bytes,
    *,
    sample_rate: int = GEMINI_TTS_SAMPLE_RATE,
    sample_width: int = 2,
    channels: int = 1,
) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    if pcm[:4] == b"RIFF":
        path.write_bytes(pcm)
        return path
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sample_width)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm)
    return path


def _concat_with_wave(paths: list[Path], dest: Path) -> Path:
    frames = bytearray()
    params: tuple[int, int, int] | None = None
    for path in paths:
        with wave.open(str(path), "rb") as wf:
            header = (wf.getnchannels(), wf.getsampwidth(), wf.getframerate())
            if params is None:
                params = header
            elif header != params:
                raise GeminiTtsError("chunk wav formats differ")
            frames.extend(wf.readframes(wf.getnframes()))
    if params is None:
        raise GeminiTtsError("no wav frames")
    with wave.open(str(dest), "wb") as out:
        out.setnchannels(params[0])
        out.setsampwidth(params[1])
        out.setframerate(params[2])
        out.writeframes(bytes(frames))
    return dest


def concat_wavs(paths: list[Path], dest: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if not paths:
        raise GeminiTtsError("no chunk wavs to concatenate")
    exe = shutil.which("ffmpeg")
    if exe:
        listing = dest.parent / "concat.txt"
        listing.write_text(
            "".join(
                "file '" + str(p.resolve()).replace("'", "'\\''") + "'\n"
                for p in paths
            ),
            encoding="utf-8",
        )
        result = subprocess.run(
            [
                exe,
                "-y",
                "-loglevel",
                "error",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(listing),
                "-ac",
                "1",
                "-ar",
                str(GEMINI_TTS_SAMPLE_RATE),
                str(dest),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            return dest
    return _concat_with_wave(paths, dest)


def _inline_audio(payload: dict[str, Any]) -> tuple[bytes, str]:
    try:
        parts = payload["candidates"][0]["content"]["parts"]
        inline = None
        for part in parts:
            inline = part.get("inlineData") or part.get("inline_data")
            if inline and inline.get("data"):
                break
        if not inline or not inline.get("data"):
            raise KeyError("inlineData")
        mime = str(inline.get("mimeType") or inline.get("mime_type") or "")
        return base64.b64decode(inline["data"]), mime
    except (KeyError, IndexError, TypeError, ValueError) as exc:
        err = payload.get("error") or payload.get("promptFeedback") or payload
        raise GeminiTtsError(f"Gemini TTS response had no audio: {err!r}") from exc


def synthesize_pcm(
    prompt: str,
    *,
    api_key: str,
    voice: str = GEMINI_TTS_VOICE,
    model: str = GEMINI_TTS_MODEL,
    client: httpx.Client | None = None,
    timeout: float = 180.0,
    retries: int = 3,
) -> bytes:
    if not api_key:
        raise GeminiTtsError(
            "GEMINI_API_KEY (or GOOGLE_API_KEY) is missing. "
            "Chunks can still be written. Operator ingest-audio still works. "
            "Do not fall back to ElevenLabs, Edge, or Kokoro from the engine."
        )
    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseModalities": ["AUDIO"],
            "speechConfig": {
                "voiceConfig": {
                    "prebuiltVoiceConfig": {"voiceName": voice}
                }
            },
        },
    }
    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": api_key,
    }
    url = (
        GEMINI_TTS_ENDPOINT
        if model == GEMINI_TTS_MODEL
        else (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{model}:generateContent"
        )
    )
    own_client = client is None
    http = client or httpx.Client(timeout=timeout)
    last_error = ""
    try:
        for attempt in range(retries):
            response = http.post(url, headers=headers, json=body)
            if response.status_code in {429, 503, 500} and attempt + 1 < retries:
                time.sleep(2 ** attempt)
                last_error = response.text[:800]
                continue
            if response.status_code >= 400:
                raise GeminiTtsError(
                    f"Gemini TTS HTTP {response.status_code}: {response.text[:800]}"
                )
            pcm, _mime = _inline_audio(response.json())
            if not pcm:
                raise GeminiTtsError("Gemini TTS returned empty audio")
            return pcm
    finally:
        if own_client:
            http.close()
    raise GeminiTtsError(last_error or "Gemini TTS failed after retries")


def write_chunk_sidecars(dest: Path, chunks: list[SpokenChunk], *, model: str, voice: str) -> Path:
    chunk_dir = dest / "audio" / "chunks"
    chunk_dir.mkdir(parents=True, exist_ok=True)
    (dest / "tts_chunks.txt").write_text(
        format_tts_chunks_file(chunks, model=model, voice=voice),
        encoding="utf-8",
    )
    for chunk in chunks:
        (chunk_dir / f"{chunk.stem()}.txt").write_text(
            chunk.transcript + "\n", encoding="utf-8"
        )
        (chunk_dir / f"{chunk.stem()}.prompt.txt").write_text(
            chunk.prompt + "\n", encoding="utf-8"
        )
    return dest / "tts_chunks.txt"


def prepare_job_chunks(
    job_id: str,
    *,
    artifacts_root: Path | None = None,
    audio_tags: bool = AUDIO_TAGS_DEFAULT,
    script: str | None = None,
) -> list[SpokenChunk]:
    dest = ensure_job_tree(job_id, root=artifacts_root)
    text = script if script is not None else (dest / "script.txt").read_text(encoding="utf-8")
    if not text.strip():
        raise GeminiTtsError(f"empty script.txt for {job_id}")
    manifest = load_manifest(job_id, root=artifacts_root)
    mode = parse_mode(manifest.channel_mode)
    chunks = chunks_for_script(text, mode=mode, audio_tags=audio_tags)
    if not transcripts_match_script(chunks, text):
        raise GeminiTtsError(
            f"TTS chunk join does not reproduce script.txt for {job_id}"
        )
    write_chunk_sidecars(
        dest,
        chunks,
        model=GEMINI_TTS_MODEL,
        voice=GEMINI_TTS_VOICE,
    )
    return chunks


def _chunk_wav_reusable(chunk_dir: Path, chunk: SpokenChunk) -> Path | None:
    wav = chunk_dir / f"{chunk.stem()}.wav"
    txt = chunk_dir / f"{chunk.stem()}.txt"
    if not wav.is_file() or wav.stat().st_size <= 44:
        return None
    if not txt.is_file():
        return None
    if normalize_ws(txt.read_text(encoding="utf-8")) != normalize_ws(chunk.transcript):
        return None
    return wav


def synthesize_job(
    job_id: str,
    *,
    artifacts_root: Path | None = None,
    voice: str = GEMINI_TTS_VOICE,
    model: str = GEMINI_TTS_MODEL,
    audio_tags: bool = AUDIO_TAGS_DEFAULT,
    force: bool = False,
    only_index: int | None = None,
    chunks_only: bool = False,
    client: httpx.Client | None = None,
    synthesize: Callable[..., bytes] | None = None,
    api_key: str | None = None,
) -> dict[str, Any]:
    dest = ensure_job_tree(job_id, root=artifacts_root)
    chunks = prepare_job_chunks(
        job_id,
        artifacts_root=artifacts_root,
        audio_tags=audio_tags,
    )
    chunk_dir = dest / "audio" / "chunks"
    key = api_key if api_key is not None else gemini_api_key()
    wavs: list[Path] = []
    synth = synthesize or (
        lambda prompt: synthesize_pcm(
            prompt, api_key=key, voice=voice, model=model, client=client
        )
    )
    if chunks_only:
        ledger = {
            "model": model,
            "voice": voice,
            "sample_rate": GEMINI_TTS_SAMPLE_RATE,
            "audio_tags": audio_tags,
            "chunks_only": True,
            "chunks": [asdict(c) | {"file": f"{c.stem()}.wav"} for c in chunks],
        }
        (chunk_dir / "ledger.json").write_text(
            json.dumps(ledger, indent=2) + "\n", encoding="utf-8"
        )
        return {
            "job_id": job_id,
            "chunk_count": len(chunks),
            "chunks_only": True,
            "tts_chunks": str(dest / "tts_chunks.txt"),
            "chunk_dir": str(chunk_dir),
        }
    if not key and synthesize is None:
        raise GeminiTtsError(
            "GEMINI_API_KEY (or GOOGLE_API_KEY) is missing. "
            f"Saved {dest / 'tts_chunks.txt'}. "
            "Set the key or python -m channel ingest-audio. "
            "The engine will not call ElevenLabs, Edge, or Kokoro."
        )
    for chunk in chunks:
        wav_path = chunk_dir / f"{chunk.stem()}.wav"
        reuse = None if force or only_index == chunk.index else _chunk_wav_reusable(
            chunk_dir, chunk
        )
        if only_index is not None and chunk.index != only_index and reuse:
            wavs.append(reuse)
            continue
        if only_index is not None and chunk.index != only_index:
            if wav_path.is_file():
                wavs.append(wav_path)
            else:
                raise GeminiTtsError(
                    f"missing {wav_path.name}; synthesize that chunk first"
                )
            continue
        if reuse is not None:
            wavs.append(reuse)
            continue
        pcm = synth(chunk.prompt)
        write_pcm_wav(wav_path, pcm)
        wavs.append(wav_path)
    concat_24k = chunk_dir / "concat_24k.wav"
    concat_wavs(wavs, concat_24k)
    ledger = {
        "model": model,
        "voice": voice,
        "sample_rate": GEMINI_TTS_SAMPLE_RATE,
        "audio_tags": audio_tags,
        "concat": "audio/chunks/concat_24k.wav",
        "chunks": [
            {
                **asdict(chunk),
                "file": f"{chunk.stem()}.wav",
                "bytes": (chunk_dir / f"{chunk.stem()}.wav").stat().st_size,
            }
            for chunk in chunks
        ],
    }
    (chunk_dir / "ledger.json").write_text(
        json.dumps(ledger, indent=2) + "\n", encoding="utf-8"
    )
    manifest = load_manifest(job_id, root=artifacts_root)
    manifest.voice = dict(GEMINI_TTS_LOCK)
    if voice != GEMINI_TTS_VOICE:
        manifest.voice["voice"] = voice
    manifest.models["tts"] = model
    manifest.paths["tts_chunks"] = str(dest / "tts_chunks.txt")
    manifest.paths["tts_chunk_dir"] = str(chunk_dir)
    manifest.paths["tts_concat"] = str(concat_24k)
    write_manifest(manifest, root=artifacts_root or ARTIFACTS)
    return {
        "job_id": job_id,
        "chunk_count": len(chunks),
        "tts_chunks": str(dest / "tts_chunks.txt"),
        "chunk_dir": str(chunk_dir),
        "concat": str(concat_24k),
        "voice": voice,
        "model": model,
    }


def under_pytest() -> bool:
    return bool(os.environ.get("PYTEST_CURRENT_TEST"))


def auto_tts_enabled(
    *,
    auto_tts: bool | None,
    smoke_test: bool,
    stubs: bool,
) -> bool:
    if smoke_test or stubs:
        return False
    if os.environ.get("CHANNEL_DISABLE_GEMINI_TTS", "").strip() in {"1", "true", "yes"}:
        return False
    if auto_tts is False:
        return False
    if auto_tts is True:
        return bool(gemini_api_key())
    if under_pytest():
        return False
    return bool(gemini_api_key())
