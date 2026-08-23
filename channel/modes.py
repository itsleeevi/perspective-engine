"""Channel mode is explicit. Do not guess it from the title alone."""

from __future__ import annotations

from enum import Enum


class ChannelMode(str, Enum):
    what_they_really_think = "what_they_really_think"
    behind_the_business = "behind_the_business"
    how_they_took_over = "how_they_took_over"


_ALIASES = {
    "what_they_really_think": ChannelMode.what_they_really_think,
    "wtrt": ChannelMode.what_they_really_think,
    "think": ChannelMode.what_they_really_think,
    "behind_the_business": ChannelMode.behind_the_business,
    "btb": ChannelMode.behind_the_business,
    "business": ChannelMode.behind_the_business,
    "how_they_really_make_money": ChannelMode.behind_the_business,
    "htrmm": ChannelMode.behind_the_business,
    "how_they_took_over": ChannelMode.how_they_took_over,
    "htto": ChannelMode.how_they_took_over,
    "took_over": ChannelMode.how_they_took_over,
    "takeover": ChannelMode.how_they_took_over,
}


CHANNEL_FLAG_HELP = (
    "what_they_really_think (default), behind_the_business "
    "(How They Really Make Money; aliases: wtrt, btb, htrmm), or "
    "how_they_took_over (aliases: htto, takeover)"
)


def parse_mode(raw: str | ChannelMode | None) -> ChannelMode:
    """Default is What They Really Think so existing commands stay unchanged."""
    if raw is None or raw == "":
        return ChannelMode.what_they_really_think
    if isinstance(raw, ChannelMode):
        return raw
    key = str(raw).strip().lower().replace("-", "_").replace(" ", "_")
    if key not in _ALIASES:
        raise ValueError(
            f"Unknown channel mode {raw!r}. Use {CHANNEL_FLAG_HELP}."
        )
    return _ALIASES[key]


def is_business(mode: str | ChannelMode | None) -> bool:
    return parse_mode(mode) is ChannelMode.behind_the_business


def is_takeover(mode: str | ChannelMode | None) -> bool:
    return parse_mode(mode) is ChannelMode.how_they_took_over


def is_company_story(mode: str | ChannelMode | None) -> bool:
    """Money-model or takeover documentaries — not historical opinion portraits."""
    parsed = parse_mode(mode)
    return parsed in (
        ChannelMode.behind_the_business,
        ChannelMode.how_they_took_over,
    )
