# Video engine (YouTube documentaries)

This is the durable specification for the **shared `channel/` engine**.
A Cloud Agent with empty chat history starts at `AGENTS.md`, then this folder.

There are two products in this repository:

1. **`channel/` YouTube documentaries** — production. Three channel modes.
2. **`graph/` LangGraph skeleton** — a different product. Do not send a real-person title through `ideate`.

## Channels

| Public name | Internal `--channel` | Playbook | Spec |
|---|---|---|---|
| What They Really Think | `what_they_really_think` | `docs/custom-videos.md` | `docs/channels/what-they-really-think.md` |
| How They Really Make Money | `behind_the_business` (alias `how_they_really_make_money`) | `docs/behind-the-business.md` | `docs/channels/how-they-really-make-money.md` |
| How They Took Over | `how_they_took_over` | `docs/how-they-took-over.md` | `docs/channels/how-they-took-over.md` |

Pass `--channel` explicitly. Do not infer the mode from the title.

## Canonical command

```text
.venv/bin/python -m channel generate --channel what_they_really_think --title "What Einstein Really Thought About God"
.venv/bin/python -m channel generate --channel behind_the_business --title "How Visa Really Makes Money"
.venv/bin/python -m channel generate --channel how_they_took_over --title "How Nvidia Took Over AI"
```

Or a job file:

```text
.venv/bin/python -m channel generate --job jobs/example.json
```

`--smoke-test` validates routing, schemas, compile, and the job tree without GenerateImage or Kokoro.

`--resume <JOB_ID>` continues an existing `artifacts/<JOB_ID>/` job.

## Do not mutate the engine

```text
DO NOT MODIFY THE VIDEO ENGINE, CHANNEL PROMPTS, GLOBAL STYLE, MODEL CONFIGURATION, OR QA THRESHOLDS DURING A NORMAL VIDEO GENERATION TASK.
```

Report a bug. Do not silently redesign the system.

## Further reading

- `PIPELINE.md` — stages, artifacts, resume
- `NARRATION.md` — voice, length, spoken English
- `VISUAL_STYLE.md` — locked styles, filenames, composition
- `QUALITY_BAR.md` — grammar of the best-performing uploads (copy grammar, never spines)
- `QUALITY_BAR_START_PROMPT.md` — paste-ready prompt that locks that grammar
- `RESEARCH.md` — sources, claims, no invention
- `ORIGINALITY.md` — score ≥ 80, monetization
- `CLOUD_AGENTS.md` — parallel jobs, secrets, environment
- `CLOUD_AGENT_START_PROMPT.md` — paste into a fresh agent
