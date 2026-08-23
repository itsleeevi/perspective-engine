"""Expand written calendar years so TTS says them as years, not as quantities.

Captions and fixtures keep digits (``1995``). The voice adapters run this
right before synthesis so Kokoro says ``nineteen ninety-five``.
"""

from __future__ import annotations

import re

_ONES = (
    "",
    "one",
    "two",
    "three",
    "four",
    "five",
    "six",
    "seven",
    "eight",
    "nine",
)
_TEENS = (
    "ten",
    "eleven",
    "twelve",
    "thirteen",
    "fourteen",
    "fifteen",
    "sixteen",
    "seventeen",
    "eighteen",
    "nineteen",
)
_TENS = (
    "",
    "",
    "twenty",
    "thirty",
    "forty",
    "fifty",
    "sixty",
    "seventy",
    "eighty",
    "ninety",
)

# 1000–2099 as a standalone token. Leaves "Windows 95", money, and 3-digit
# counts alone.
_YEAR = re.compile(r"\b((?:1[0-9]{3})|(?:20[0-9]{2}))\b")

_TENS_WORD = (
    r"(?:twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety)"
    r"(?:-(?:one|two|three|four|five|six|seven|eight|nine))?"
)
_TEENS_WORD = (
    r"(?:ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|"
    r"seventeen|eighteen|nineteen)"
)
_ONES_WORD = r"(?:one|two|three|four|five|six|seven|eight|nine)"

# Spelled-out calendar years. Does not match "eighteen months" or "twenty people".
SPELLED_YEAR = re.compile(
    rf"\b(?:eighteen|nineteen)\s+"
    rf"(?:oh\s+{_ONES_WORD}|hundred|{_TEENS_WORD}|{_TENS_WORD})\b"
    rf"|\btwenty\s+(?:oh\s+{_ONES_WORD}|{_TEENS_WORD}|{_TENS_WORD})\b"
    rf"|\btwo thousand(?:\s+(?:and\s+)?{_ONES_WORD})\b",
    re.I,
)


def year_to_words(year: int) -> str:
    """American spoken year: 1995 → nineteen ninety-five, 2011 → twenty eleven."""
    if year == 2000:
        return "two thousand"
    if 2001 <= year <= 2009:
        return f"two thousand {_ONES[year % 10]}"
    if 2010 <= year <= 2099:
        return f"twenty {_two_digit(year % 100)}"
    century, rest = divmod(year, 100)
    head = _two_digit(century)
    if rest == 0:
        return f"{head} hundred"
    if rest < 10:
        return f"{head} oh {_ONES[rest]}"
    return f"{head} {_two_digit(rest)}"


def _two_digit(n: int) -> str:
    if n < 10:
        return _ONES[n]
    if n < 20:
        return _TEENS[n - 10]
    tens, ones = divmod(n, 10)
    if ones == 0:
        return _TENS[tens]
    return f"{_TENS[tens]}-{_ONES[ones]}"


def speak_years(text: str) -> str:
    """Replace 4-digit calendar years with the words a narrator should say."""

    def repl(match: re.Match[str]) -> str:
        return year_to_words(int(match.group(1)))

    return _YEAR.sub(repl, text)
