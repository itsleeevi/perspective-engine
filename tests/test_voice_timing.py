"""
Tests for the pure word-boundary timing math that lets a continuously-
synthesised speech run (multiple narration beats spoken without artificial
pauses) be sliced back into exact per-shot durations, and for the word
alignment that feeds it.

This is the crux of both the "natural storytelling narration" requirement
(shots must still get individually correct durations even though nothing
separates them acoustically) and the "scene changes must line up with the
narration" requirement (a single mismatched word must not blow up timing
precision for every other beat sharing its speech run).
"""

from __future__ import annotations

from adapters.voice.edge import _align_word_offsets, split_run_durations


class TestAlignWordOffsets:
    def test_one_to_one_match(self):
        naive = ["Level", "one,", "the", "applicant."]
        events = [("Level", 0.0, 0.2), ("one,", 0.3, 0.2), ("the", 0.6, 0.1), ("applicant.", 0.8, 0.3)]
        offsets = _align_word_offsets(naive, events)
        assert offsets == [0.0, 0.3, 0.6, 0.8]

    def test_edge_tts_merges_number_and_unit_into_one_event(self):
        """
        Regression test for the real observed quirk: edge-tts's tokeniser
        reads "30,000 ft" as a single spoken token where a naive split keeps
        them as two words. Both naive words must resolve to that one event's
        offset instead of the whole run falling back to proportional timing.
        """
        naive = ["Free", "falling", "from", "30,000", "ft,", "combat"]
        events = [
            ("Free", 0.0, 0.2),
            ("falling", 0.3, 0.2),
            ("from", 0.6, 0.15),
            ("30,000 ft,", 0.9, 0.5),  # merged event for two naive words
            ("combat", 1.5, 0.3),
        ]
        offsets = _align_word_offsets(naive, events)
        assert offsets == [0.0, 0.3, 0.6, 0.9, 0.9, 1.5]

    def test_naive_word_split_into_multiple_events(self):
        """The reverse direction: one naive word spoken as multiple events."""
        naive = ["five-mile", "run"]
        events = [("five-mile", 0.0, 0.15), ("run", 0.4, 0.2)]
        # Sanity check for the common case still works when nothing merges.
        assert _align_word_offsets(naive, events) == [0.0, 0.4]

        events_split = [("five", 0.0, 0.1), ("mile", 0.2, 0.15), ("run", 0.4, 0.2)]
        offsets = _align_word_offsets(naive, events_split)
        assert offsets == [0.0, 0.4]

    def test_unreconcilable_sequences_return_none(self):
        naive = ["completely", "different", "words"]
        events = [("nothing", 0.0, 0.2), ("matches", 0.3, 0.2), ("here", 0.6, 0.2)]
        assert _align_word_offsets(naive, events) is None


class TestSplitRunDurations:
    def test_single_beat_gets_full_duration(self):
        word_counts = [3]
        offsets = [0.0, 0.3, 0.6]
        durations = split_run_durations(word_counts, offsets, run_total_seconds=1.0)
        assert durations == [1.0]

    def test_durations_sum_to_run_total(self):
        word_counts = [2, 3, 1]
        offsets = [0.0, 0.3, 0.6, 0.9, 1.2, 1.4]
        run_total = 1.6
        durations = split_run_durations(word_counts, offsets, run_total)
        assert len(durations) == 3
        assert round(sum(durations), 3) == round(run_total, 3)

    def test_first_beat_absorbs_lead_in_silence(self):
        """
        The first word doesn't start at t=0 (edge-tts adds a small lead-in);
        that silence must be credited to the first beat, not dropped from the
        timeline entirely.
        """
        word_counts = [1, 1]
        offsets = [0.25, 0.6]
        durations = split_run_durations(
            word_counts, offsets, run_total_seconds=1.0, cut_lead_seconds=0.0
        )
        assert durations[0] == 0.6  # from t=0 up to beat 2's first word
        assert durations[1] == 0.4  # from beat 2's first word to the end

    def test_trailing_pause_credited_to_preceding_beat(self):
        word_counts = [1, 1]
        offsets = [0.0, 0.3]
        run_total = 2.0  # a long trailing pause after the last word
        durations = split_run_durations(
            word_counts, offsets, run_total, cut_lead_seconds=0.0
        )
        assert durations[0] == 0.3
        assert durations[1] == 1.7

    def test_cut_lead_moves_the_boundary_earlier_without_changing_the_total(self):
        """
        Each image comes up slightly before its narration starts (picture
        leads sound, and TTS word timings trail the audible onset). The lead
        must move the boundary only — never the run total, or the picture
        would drift away from the audio over a long video.
        """
        word_counts = [1, 1]
        offsets = [0.0, 1.0]
        run_total = 2.0

        durations = split_run_durations(
            word_counts, offsets, run_total, cut_lead_seconds=0.12
        )

        assert durations[0] == 0.88  # beat 2's image is up 120 ms early
        assert durations[1] == 1.12
        assert round(sum(durations), 3) == run_total

    def test_cut_lead_never_inverts_very_short_beats(self):
        """
        On beats shorter than the lead itself, boundaries must stay ordered
        rather than running backwards past each other.
        """
        word_counts = [1, 1, 1]
        offsets = [0.0, 0.05, 0.09]

        durations = split_run_durations(
            word_counts, offsets, run_total_seconds=0.5, cut_lead_seconds=0.12
        )

        assert all(d >= 0.0 for d in durations)
        assert round(sum(durations), 3) == 0.5

    def test_empty_word_counts_returns_empty(self):
        assert split_run_durations([], [], run_total_seconds=0.0) == []
        # A run made up entirely of zero-word beats has nothing to time.
        assert split_run_durations([0], [], run_total_seconds=0.0) == []

    def test_failed_alignment_falls_back_to_proportional(self):
        """
        If word alignment fails entirely (``None``), the function must never
        crash or misalign — it falls back to proportional distribution that
        still sums to the run total.
        """
        word_counts = [2, 2]
        durations = split_run_durations(word_counts, None, run_total_seconds=2.0)
        assert durations == [1.0, 1.0]

    def test_offset_count_mismatch_falls_back_to_proportional(self):
        word_counts = [2, 2]
        offsets = [0.0, 0.2, 0.4]  # only 3 offsets, not 4
        durations = split_run_durations(word_counts, offsets, run_total_seconds=2.0)
        assert durations == [1.0, 1.0]

    def test_zero_word_beat_in_fallback_gets_zero(self):
        word_counts = [0, 4]
        durations = split_run_durations(word_counts, None, run_total_seconds=2.0)
        assert durations == [0.0, 2.0]
