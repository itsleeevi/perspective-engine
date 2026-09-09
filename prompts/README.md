# Prompts (index)

Production stage prompts stay in versioned Python modules so `stage_prompts_for` cannot drift from the code path. Do not copy them here.

The staged **master prompt** is `channel/master_prompt.py` (`MASTER` on each module): same operator loop, channel-specific DNA.

| Channel | Module |
|---|---|
| What They Really Think | `channel/agent_prompts.py` |
| How They Really Make Money | `channel/business_prompts.py` |
| How They Took Over | `channel/takeover_prompts.py` |
| Quiet Wealth | `channel/wealth_prompts.py` (`MASTER` is the v5 long-form wealth POV prompt in `channel/wealth_pov_master_v5.txt`) |

Shared image assembly: `channel/prompts.py`. Cinema grammar: `channel/quality_bar.py` (`docs/video-engine/QUALITY_BAR.md`). Versions: `channel/engine.py` (`PROMPT_VERSION`).

Normal generation treats these files as read-only.
