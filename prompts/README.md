# Prompts (index)

Production stage prompts stay in versioned Python modules so `stage_prompts_for` cannot drift from the code path. Do not copy them here.

| Channel | Module |
|---|---|
| What They Really Think | `channel/agent_prompts.py` |
| How They Really Make Money | `channel/business_prompts.py` |
| How They Took Over | `channel/takeover_prompts.py` |

Shared image assembly: `channel/prompts.py`. Cinema grammar: `channel/quality_bar.py` (`docs/video-engine/QUALITY_BAR.md`). Versions: `channel/engine.py` (`PROMPT_VERSION`).

Normal generation treats these files as read-only.
