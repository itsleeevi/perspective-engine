"""Dispatch stage prompts by channel mode. WTRT stays on agent_prompts."""

from __future__ import annotations

from types import ModuleType

from channel.modes import ChannelMode, is_business, parse_mode


def stage_prompts_for(mode: ChannelMode | str | None = None) -> ModuleType:
    if is_business(mode):
        from channel import business_prompts

        return business_prompts
    from channel import agent_prompts

    return agent_prompts


def researcher_prompt(mode: ChannelMode | str | None = None) -> str:
    return stage_prompts_for(mode).RESEARCHER
