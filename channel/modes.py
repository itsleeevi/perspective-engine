"""Channel mode is explicit. Do not guess it from the title alone."""

from __future__ import annotations

from enum import Enum


class ChannelMode(str, Enum):
    what_they_really_think = "what_they_really_think"
    behind_the_business = "behind_the_business"


_ALIASES = {
    "what_they_really_think": ChannelMode.what_they_really_think,
    "wtrt": ChannelMode.what_they_really_think,
    "think": ChannelMode.what_they_really_think,
    "behind_the_business": ChannelMode.behind_the_business,
    "btb": ChannelMode.behind_the_business,
    "business": ChannelMode.behind_the_business,
}


def parse_mode(raw: str | ChannelMode | None) -> ChannelMode:
    """Default is What They Really Think so existing commands stay unchanged."""
    if raw is None or raw == "":
        return ChannelMode.what_they_really_think
    if isinstance(raw, ChannelMode):
        return raw
    key = str(raw).strip().lower().replace("-", "_").replace(" ", "_")
    if key not in _ALIASES:
        raise ValueError(
            f"Unknown channel mode {raw!r}. Use what_they_really_think or "
            "behind_the_business (aliases: wtrt, btb)."
        )
    return _ALIASES[key]


def is_business(mode: str | ChannelMode | None) -> bool:
    return parse_mode(mode) is ChannelMode.behind_the_business
