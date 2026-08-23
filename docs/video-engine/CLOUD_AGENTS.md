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

Documentary generation does **not** need `OPENAI_API_KEY`, `FAL_KEY`, or `ELEVENLABS_API_KEY`. Those belong to the unused `graph/` Phase-2 adapters. If a required documentary tool is missing (Kokoro, GenerateImage), **stop**. Do not silently switch providers.

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

Wikipedia (seed), company IR / SEC sites (agent research), Cursor GenerateImage. No hidden model “latest”.
