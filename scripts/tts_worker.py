"""
Chatterbox TTS worker — runs inside the isolated ``.venv-tts`` interpreter.

The main pipeline venv stays torch-free: `adapters/voice/chatterbox.py`
invokes this script as a subprocess with a JSON job on stdin and reads a
JSON result from stdout. One invocation loads the model once and
synthesises every pack, so per-pack model-load cost is not paid 20 times.

Job format (stdin):
    {
      "packs":        ["text of pack 0", "text of pack 1", ...],
      "out_dir":      "/tmp/...",           # wavs are written here
      "voice_ref":    "/path/to/ref.wav",   # optional, 5-10s reference clip
      "exaggeration": 0.5,                  # chatterbox emotion dial
      "cfg_weight":   0.5,
      "model":        "turbo"               # "turbo" (350M) or "nano" (110M)
    }

Result format (stdout, single line):
    {
      "sr": 24000,
      "packs": [
        {"wav": "/tmp/.../pack_000.wav",
         "duration": 21.4,
         "words": [["They", 0.07], ["kicked", 0.31], ...]},
        ...
      ]
    }

Word timings come from forced alignment (faster-whisper, word_timestamps),
NOT from the TTS engine — that is what makes the sync engine-independent:
any future voice that can produce a wav can be timed the same way.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def _load_tts(model_kind: str):
    import torch

    torch.set_default_dtype(torch.float32)
    from chatterbox.tts_turbo import ChatterboxTurboTTS

    # chatterbox-tts 0.1.7 exposes only Turbo (350M) through from_pretrained;
    # it ships a built-in narrator so no reference clip is required.
    tts = ChatterboxTurboTTS.from_pretrained(device="cpu")
    # CPU path: s3tokenizer mel filters can land in float64 and crash matmul
    # against float32 spectrograms when cloning a reference voice.
    tok = getattr(getattr(tts, "s3gen", None), "tokenizer", None)
    if tok is not None:
        orig = tok.log_mel_spectrogram

        def _log_mel_f32(audio, padding=0):
            import numpy as np

            if not torch.is_tensor(audio):
                audio = np.asarray(audio, dtype=np.float32)
            elif audio.dtype != torch.float32:
                audio = audio.float()
            return orig(audio, padding=padding)

        tok.log_mel_spectrogram = _log_mel_f32
    return tts


def _load_aligner():
    from faster_whisper import WhisperModel

    # base.en int8 on CPU: fast, and accurate enough for word starts — the
    # text is already known, we only need the clock, not the transcript.
    return WhisperModel("base.en", device="cpu", compute_type="int8")


def _align(aligner, wav_path: Path) -> list[tuple[str, float]]:
    segments, _info = aligner.transcribe(
        str(wav_path), word_timestamps=True, language="en", beam_size=1
    )
    words: list[tuple[str, float]] = []
    for seg in segments:
        for w in seg.words or []:
            words.append((w.word.strip(), float(w.start)))
    return words


def main() -> None:
    job = json.loads(sys.stdin.read())
    out_dir = Path(job["out_dir"])
    out_dir.mkdir(parents=True, exist_ok=True)

    tts = _load_tts(job.get("model", "turbo"))
    aligner = _load_aligner()

    import soundfile as sf

    # Prosody knobs. Turbo's sampler drives how alive the read feels:
    # temperature under ~0.7 flattens into newsreader, above ~1.0 starts to
    # wander; 0.9 with a light repetition penalty keeps sentence melodies
    # varied without artifacts.
    gen_kwargs: dict = {
        "temperature": float(job.get("temperature", 0.9)),
        "top_p": float(job.get("top_p", 0.95)),
        "repetition_penalty": float(job.get("repetition_penalty", 1.2)),
    }
    voice_ref = job.get("voice_ref") or None
    if voice_ref:
        # exaggeration only applies while conditioning on a reference clip;
        # condition once, then reuse for every pack.
        tts.prepare_conditionals(
            voice_ref, exaggeration=float(job.get("exaggeration", 0.5))
        )

    results = []
    for i, text in enumerate(job["packs"]):
        wav = tts.generate(text, **gen_kwargs)
        wav_path = out_dir / f"pack_{i:03d}.wav"
        data = wav.squeeze(0).cpu().numpy()
        sf.write(wav_path, data, tts.sr)
        duration = len(data) / tts.sr
        words = _align(aligner, wav_path)
        results.append(
            {
                "wav": str(wav_path),
                "duration": round(duration, 3),
                "words": [[w, round(t, 3)] for w, t in words],
            }
        )
        print(f"pack {i}: {duration:.1f}s, {len(words)} words", file=sys.stderr)

    print(json.dumps({"sr": tts.sr, "packs": results}))


if __name__ == "__main__":
    main()
