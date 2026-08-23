"""Slugs whose assembled stills and voice must not change on recompile.

Person names may appear here as path slugs. Keep them out of
``channel/config.py`` — that file is scanned for leaked subjects.
"""

from __future__ import annotations

# Shipped channel cuts. Rebuilds keep am_liam and the frozen global style
# (no new palette accent). New titles hash the slug for voice + accent.
SHIPPED_STYLE_LOCK = frozenset(
    {
        "elon-musk-ai",
        "jeff-bezos-elon-musk",
        "sam-altman-the-future-of-work",
        "steve-jobs-bill-gates",
        "einstein-religion",
        "einstein-zionism",
        "darwin-human-nature",
        "stalin_hitler",
        "hitler_americans",
        "putin_americans",
        "kremlin_americans",
        "visa-really-makes-money",
        "costco-really-makes-money",
    }
)

# New titles never go slower than this. Shipped recuts may be locked below.
KOKORO_SPEED_MIN = 1.0

# Per-slug Kokoro speed when it must not follow the channel default.
KOKORO_SPEED_LOCK = {
    "visa-really-makes-money": 1.15,
    "costco-really-makes-money": 0.92,
}
