"""
Free Microsoft Edge TTS voice adapter (no API key, no metered cost).

Consecutive narrated shots are synthesised as ONE continuous utterance rather
than one TTS call per shot. This matters for two reasons:

1. Natural delivery. With shots now cut every 2-3 seconds, synthesising each
   one separately and stitching them with an artificial pause would make the
   narration sound like a slideshow reading out captions instead of a person
   telling a story — the opposite of what this format needs.
2. Exact per-shot timing without an artificial pause to eat the rounding
   error. edge-tts can report the offset and duration of every spoken WORD
   within a synthesis (``boundary="WordBoundary"``). Since every shot's
   narration text is known in advance (``script_fixture.split_beat_into_chunks``
   decided it), the word-boundary stream is walked in lockstep with the shot
   list to read off each shot's exact (start, end) inside the one continuous
   recording — the same technique auto-generated YouTube captions use, just
   run in the opposite direction (we already know the text; we are timing it).
   edge-tts's own tokeniser occasionally disagrees with a naive word split
   (e.g. it reads "30,000 ft" as one spoken token), so the two are
   reconciled by ``_align_word_offsets`` rather than assumed to already
   match — see that function's docstring for why this matters for a format
   this dense with numbers.

A run of consecutive empty (deliberately unnarrated) shots breaks the
continuous utterance: there is nothing to synthesise for them, so they get a
dedicated silent segment of their own requested duration instead, and speech
resumes as a new continuous run after the gap.
"""

from __future__ import annotations

import asyncio
import hashlib
import re
import tempfile
from pathlib import Path

import edge_tts

from adapters import _cache
from adapters.voice import _audio
from adapters.voice.base import VoiceAdapter, VoiceoverResult
from adapters.voice.years import speak_years
from graph.assets import save_asset

# AndrewMultilingual is one of Microsoft's newer "Multilingual" neural
# voices (still free via edge-tts) built on a more recent, more expressive
# TTS model than the older regional voices like ChristopherNeural; it is the
# voice most faceless-narration channels in this exact format use because it
# reads long-form prose with less of the flat, "reading captions aloud"
# quality older neural voices have. Compare it against alternatives yourself
# with `python -m cli.run --voice <name>`; other reasonable options are
# en-US-BrianMultilingualNeural (warmer, more casual) and en-US-GuyNeural
# (older-generation, punchier delivery).
_DEFAULT_VOICE = "en-US-AndrewMultilingualNeural"
_RATE = "-8%"
_PITCH = "-2Hz"

_SAMPLE_RATE = 24000
_BITRATE = "128k"

# edge-tts reports word timing in 100-nanosecond ticks.
_TICKS_PER_SECOND = 10_000_000.0


async def _synthesize_with_word_boundaries(
    text: str, voice: str
) -> tuple[bytes, list[tuple[str, float, float]]]:
    """
    Synthesise ``text`` as one utterance, returning (mp3 bytes, word events).

    Each word event is ``(text, offset_seconds, duration_seconds)``, in the
    same order the words appear in ``text``. The event text is kept (not
    discarded) so the caller can align it against its own ``str.split()`` of
    the beat text even when edge-tts's TTS-oriented tokeniser disagrees with
    a naive split — see ``_align_word_offsets``.
    """
    communicate = edge_tts.Communicate(
        text, voice, rate=_RATE, pitch=_PITCH, boundary="WordBoundary"
    )
    audio_chunks: list[bytes] = []
    words: list[tuple[str, float, float]] = []
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_chunks.append(chunk["data"])
        elif chunk["type"] == "WordBoundary":
            words.append((
                chunk["text"],
                chunk["offset"] / _TICKS_PER_SECOND,
                chunk["duration"] / _TICKS_PER_SECOND,
            ))
    if not audio_chunks:
        raise RuntimeError("edge-tts returned no audio data.")
    return b"".join(audio_chunks), words


def _normalize_word(word: str) -> str:
    return re.sub(r"[^0-9a-zA-Z]", "", word).lower()


def _align_word_offsets(
    naive_words: list[str], events: list[tuple[str, float, float]]
) -> list[float] | None:
    """
    Map each word in ``naive_words`` (plain ``str.split()`` of the beat
    texts, which is what shot boundaries are counted against) to the start
    offset of the matching edge-tts WordBoundary event.

    The two tokenisations usually agree one-to-one, but edge-tts's
    TTS-oriented tokeniser sometimes reads a number and its adjoining unit as
    a single spoken token where a naive split keeps them separate — e.g.
    "30,000 ft" arrives as ONE event for the two naive words "30,000" and
    "ft" (observed in practice with distances, ages, and quantities, which
    this narrated-career-ladder format uses constantly). The reverse also
    happens on rare compounds. Treating any such mismatch as fatal (the old
    behaviour) forced proportional-by-word-count timing across the *entire*
    speech run for every beat that shared it with the mismatched word, which
    silently discarded real pacing (pauses, emphasis) for potentially many
    shots at once just because one word merged.

    This walks both sequences together, and on a mismatch tries collapsing a
    short run (1-3) of naive words or of events — in either direction —
    until their normalised (alphanumeric, lowercased) text matches, before
    continuing. A merged group of naive words all take the one event's
    offset (sub-word precision is lost only for the handful of words the
    quirk actually touches, not the whole run).

    Returns ``None`` if the sequences can't be reconciled at all (not
    observed in testing, but the caller must degrade safely: proportional
    distribution for the whole run, same as before this alignment existed).
    """
    offsets: list[float] = []
    ni = ei = 0
    n_words, n_events = len(naive_words), len(events)
    while ni < n_words:
        if ei >= n_events:
            return None
        matched = False
        for span in (1, 2, 3):
            if ni + span > n_words:
                break
            merged = "".join(_normalize_word(w) for w in naive_words[ni : ni + span])
            if merged == _normalize_word(events[ei][0]):
                offsets.extend([events[ei][1]] * span)
                ni += span
                ei += 1
                matched = True
                break
        if matched:
            continue
        for span in (2, 3):
            if ei + span > n_events:
                break
            merged = "".join(_normalize_word(t) for t, _, _ in events[ei : ei + span])
            if merged == _normalize_word(naive_words[ni]):
                offsets.append(events[ei][1])
                ni += 1
                ei += span
                matched = True
                break
        if not matched:
            return None
    return offsets


# How far before a beat's first spoken word its image appears.
#
# A cut placed exactly on the reported word-start reads as slightly late, for
# two compounding reasons. First, TTS word timings mark the start of the
# word's nucleus, while the ear registers the preceding breath and consonant
# onset: measuring a rendered sample against speech onsets detected in its own
# audio, reported word starts trailed the audible onset by 77-176 ms.
# Second, film convention is that picture leads sound — an editor cuts a few
# frames early so the new image is already on screen when the new phrase
# arrives. This lead covers both; it is deliberately smaller than the shortest
# sentence pause so a cut still lands inside silence, never over the tail of
# the previous phrase.
CUT_LEAD_SECONDS = 0.12


def split_run_durations(
    word_counts: list[int],
    word_offsets: list[float] | None,
    run_total_seconds: float,
    cut_lead_seconds: float = CUT_LEAD_SECONDS,
) -> list[float]:
    """
    Assign each beat in a continuous speech run its exact on-screen duration.

    ``word_counts[i]`` is how many words beat *i* contributes, in order.
    ``word_offsets`` is one start offset per word across the whole run
    (produced by ``_align_word_offsets``), or ``None`` if alignment failed
    entirely.

    Beat *i*'s duration runs from just before its first word to just before
    the next beat's first word (or the end of the run, for the last beat) —
    the trailing pause after a sentence is credited to the beat that ends on
    it, minus ``cut_lead_seconds`` handed to the next beat so its image is up
    fractionally before its narration starts (see ``CUT_LEAD_SECONDS``). The
    very first beat's duration is measured from the start of the run's audio
    (time 0), not from its first word's offset, so any lead-in silence before
    the first word is credited to it rather than silently dropped.

    Durations always sum to ``run_total_seconds``: the lead shifts interior
    boundaries without changing the total, so the picture cannot drift away
    from the audio no matter how many beats a run contains.

    If alignment failed, duration is instead distributed proportionally by
    word count — less precise, but never misaligned or crashing.
    """
    total_expected = sum(word_counts)
    if total_expected == 0:
        return []
    if word_offsets is None or total_expected != len(word_offsets):
        return [
            round(run_total_seconds * n / total_expected, 3) if n else 0.0
            for n in word_counts
        ]

    # boundaries[0] is always 0.0 (the start of the run's audio, crediting any
    # lead-in silence before the first word to the first beat); boundaries[i]
    # for 0 < i < len(word_counts) is just before beat i's first word;
    # boundaries[-1] is the end of the run's audio.
    boundaries = [0.0]
    cursor = 0
    for n in word_counts[:-1]:
        cursor += n
        # Never pull a boundary back past the previous one: on a run of very
        # short beats the lead could otherwise invert their order.
        boundaries.append(
            max(boundaries[-1], word_offsets[cursor] - cut_lead_seconds)
        )
    boundaries.append(max(boundaries[-1], run_total_seconds))

    return [
        round(max(0.0, boundaries[i + 1] - boundaries[i]), 3)
        for i in range(len(word_counts))
    ]


class EdgeTTSVoiceAdapter(VoiceAdapter):
    """Free neural TTS via edge-tts, with word-level timing measurement."""

    def __init__(self, voice: str = _DEFAULT_VOICE) -> None:
        self._voice = voice

    async def synthesize(
        self,
        script_beats: list[str],
        shot_durations: list[float],
        voice_id: str = "default",
    ) -> VoiceoverResult:
        """
        Synthesise one audio track for the whole script.

        ``script_beats`` is shot-aligned: entry *i* is the narration for shot
        *i*. Consecutive non-empty entries are spoken as one continuous
        utterance (see module docstring); an empty entry is a deliberate gap
        and gets ``shot_durations[i]`` of real silence instead.
        """
        if not script_beats:
            script_beats = ["Perspective shift."]
        resolved_voice = self._voice if voice_id == "default" else voice_id

        cache_key = _cache.make_key(
            {
                "provider": "edge-tts",
                "voice": resolved_voice,
                "rate": _RATE,
                "pitch": _PITCH,
                "year_speak": 1,
                "beats": list(script_beats),
                "silences": [
                    shot_durations[i] if i < len(shot_durations) else 0.0
                    for i, b in enumerate(script_beats)
                    if not (b or "").strip()
                ],
            }
        )
        cached = _cache.load("edge_tts_voiceover", cache_key)
        if cached is not None:
            # A cache hit makes no new API call, and edge-tts is free regardless.
            return VoiceoverResult(
                audio_url=cached["audio_url"],
                duration_seconds=cached["duration_seconds"],
                beat_durations=cached["beat_durations"],
                cost_usd=0.0,
            )

        # Group into alternating (speech run) / (single silent gap) segments,
        # preserving beat order so concatenation reproduces the script.
        segments: list[tuple[str, list[int]]] = []  # ("speech"|"silence", beat indices)
        run: list[int] = []
        for i, raw in enumerate(script_beats):
            if (raw or "").strip():
                run.append(i)
            else:
                if run:
                    segments.append(("speech", run))
                    run = []
                segments.append(("silence", [i]))
        if run:
            segments.append(("speech", run))

        spoken_beats = [
            speak_years(raw.strip()) if (raw or "").strip() else (raw or "")
            for raw in script_beats
        ]

        beat_durations: list[float] = [0.0] * len(script_beats)

        with tempfile.TemporaryDirectory(prefix="pe_edge_") as tmp:
            tmp_path = Path(tmp)
            parts: list[Path] = []

            for seg_idx, (kind, indices) in enumerate(segments):
                part = tmp_path / f"seg_{seg_idx:03d}.mp3"
                if kind == "silence":
                    i = indices[0]
                    gap = shot_durations[i] if i < len(shot_durations) else 1.0
                    await asyncio.to_thread(_audio.silence_mp3, part, gap, _SAMPLE_RATE)
                    beat_durations[i] = round(gap, 3)
                else:
                    text = " ".join(spoken_beats[i].strip() for i in indices)
                    audio_bytes, word_events = await _synthesize_with_word_boundaries(
                        text, resolved_voice
                    )
                    part.write_bytes(audio_bytes)
                    run_total = await asyncio.to_thread(_audio.duration_seconds, part)
                    beat_words = [spoken_beats[i].strip().split() for i in indices]
                    word_counts = [len(w) for w in beat_words]
                    naive_words = [w for beat in beat_words for w in beat]
                    word_offsets = _align_word_offsets(naive_words, word_events)
                    durations = split_run_durations(word_counts, word_offsets, run_total)
                    for i, d in zip(indices, durations, strict=True):
                        beat_durations[i] = d
                parts.append(part)

            out = tmp_path / "full.mp3"
            await asyncio.to_thread(_audio.concat_mp3, parts, out, _SAMPLE_RATE)
            audio_bytes = out.read_bytes()
            total = await asyncio.to_thread(_audio.duration_seconds, out)

        digest = hashlib.sha1("\n".join(script_beats).encode("utf-8")).hexdigest()[:16]
        url = save_asset(f"audio/voiceover_edge_{digest}.mp3", audio_bytes)

        _cache.store(
            "edge_tts_voiceover",
            cache_key,
            {
                "audio_url": url,
                "duration_seconds": total,
                "beat_durations": beat_durations,
            },
        )
        return VoiceoverResult(
            audio_url=url,
            duration_seconds=total,
            beat_durations=beat_durations,
            cost_usd=0.0,
        )
