# Working video projects

Canonical Cloud / parallel-safe path writes an isolated job under `artifacts/<JOB_ID>/`:

```text
.venv/bin/python -m channel generate --channel <mode> --title "…"
```

Sequential local init still writes a folder here:

```text
.venv/bin/python -m channel init --channel <mode> "What X Really Thought About Y"
```

`project.json` is the shared context (research, story, bibles, scenes).
Do not commit these folders; compiled fixtures live in `fixtures/`. Parallel jobs must not clobber repo-root `fixtures/`.
