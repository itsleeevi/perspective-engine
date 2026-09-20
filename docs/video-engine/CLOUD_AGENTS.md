# Cloud Agents

`NEW_AGENT_CHAT_HISTORY = EMPTY`. Read `AGENTS.md` and `.cursor/rules/`.

## Setup

```text
python3.13 -m venv .venv
.venv/bin/pip install -e ".[dev]"
# ffmpeg required before assemble, not before generate --smoke-test
.venv/bin/python -m channel cloud-readiness
```

`.cursor/environment.json` installs the Python package and ffmpeg when the Cloud snapshot supports it.

## Secrets

Documentary generation does **not** need `OPENAI_API_KEY`, `FAL_KEY`, or `ELEVENLABS_API_KEY`. Those belong to the unused `graph/` Phase-2 adapters. The engine never calls those APIs. Gemini TTS uses `GEMINI_API_KEY` (`python -m channel tts`). Opt-in stills use the same key (`python -m channel images`, Nano Banana 2 / `gemini-3.1-flash-image`) and do not run on `--resume`. Opt-in clips use the same key (`python -m channel videos`, `gemini-omni-1.1-flash`) and also do not run on `--resume`. Opt-in music uses the same key (`python -m channel music`, `lyria-3-clip-preview`) and also does not run on `--resume`. A Cloud agent fills research + narration, then stops at `WAIT_AUDIO` unless that key is set. Drop-folder cuts (`python -m channel drop`) wait for operator stills named `[00-00]_….jpg` plus audio, then assemble without burned captions.

Names only: `.env.example`. Never commit `.env`.

## Parallel

Each `generate` owns `artifacts/<JOB_ID>/`. Do not write compiled fixtures to the repo-root `fixtures/` from a Cloud job. Do not edit `channel/config.py`, prompt modules, or QA thresholds.

Agents A/B/C may run Einstein, Visa, and Nvidia at the same time if job IDs differ.

## Artifacts

Do not commit `.mp4` files. Report:

- job ID
- `artifacts/<id>/final/` paths once assembled
- thumbnail / Short paths
- QA scores from `report.txt`

## Network

Wikipedia (seed), company IR / SEC sites (agent research), Gemini TTS, Nano Banana 2 stills, and Omni 1.1 Flash clips (`generativelanguage.googleapis.com`) when `GEMINI_API_KEY` is set. No hidden model “latest”. Operator Google Flow stills remain valid. Voice is Gemini TTS or imported audio.
