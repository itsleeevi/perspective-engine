"""
Tests for ``_cumulative_frame_counts``, the frame-boundary snapping that
keeps a long, many-shot concatenated video's picture cuts aligned with the
narration timeline.

Regression coverage for a real drift bug: naively rounding each shot's own
duration up to a whole frame (``ceil(duration * fps)``) leaves up to one
frame of remainder *per shot*, and concatenated segments only ever add that
remainder in the same direction. With shots averaging 2-3 seconds, a
15-25 minute video (300-600 shots) could drift the picture multiple seconds
behind the narration by the end — exactly the "scene changes don't line up
with the narration" symptom this fixes.
"""

from __future__ import annotations

from graph.nodes.assemble import _cumulative_frame_counts

FPS = 30


class TestCumulativeFrameCounts:
    def test_empty_input(self):
        assert _cumulative_frame_counts([], FPS) == []

    def test_exact_frame_durations_round_trip(self):
        # 1s, 2s at 30fps are exact frame counts already.
        assert _cumulative_frame_counts([1.0, 2.0], FPS) == [30, 60]

    def test_frame_counts_sum_covers_total_duration(self):
        """
        The concatenated segment length (in frames) must always be enough to
        cover the full narration duration -- never shorter, so the audio mux
        never has to clip the narration.
        """
        durations = [2.4, 2.6, 2.5, 2.9, 2.1, 2.7, 2.3, 2.8] * 20  # 160 shots
        total_seconds = sum(durations)
        counts = _cumulative_frame_counts(durations, FPS)
        assert len(counts) == len(durations)
        assert sum(counts) / FPS >= total_seconds - 1e-6

    def test_no_drift_regardless_of_shot_count(self):
        """
        The naive independent-rounding approach drifts without bound as shot
        count grows (worst case ~0.5 frame/shot in one direction). Cumulative
        snapping must keep every boundary within one frame of the true
        narration timeline even across hundreds of shots.
        """
        durations = [2.37] * 500  # a value that rounds awkwardly at 30fps
        counts = _cumulative_frame_counts(durations, FPS)

        cumulative_seconds = 0.0
        cumulative_frames = 0
        max_drift_frames = 0.0
        for d, frames in zip(durations, counts, strict=True):
            cumulative_seconds += d
            cumulative_frames += frames
            true_frame = cumulative_seconds * FPS
            drift = abs(cumulative_frames - true_frame)
            max_drift_frames = max(max_drift_frames, drift)

        assert max_drift_frames < 1.0001

    def test_naive_per_shot_rounding_would_have_drifted(self):
        """
        Sanity check that this scenario actually exercises the bug: the old
        per-shot ``ceil`` approach drifts far more than 1 frame over the same
        input, proving the fix isn't a no-op.
        """
        import math

        durations = [2.37] * 500
        naive_total_frames = sum(math.ceil(d * FPS) for d in durations)
        true_total_frames = sum(durations) * FPS
        naive_drift = naive_total_frames - true_total_frames
        assert naive_drift > 100  # several seconds of drift at 30fps

    def test_every_shot_gets_at_least_one_frame(self):
        counts = _cumulative_frame_counts([0.001, 0.001, 0.001], FPS)
        assert all(c >= 1 for c in counts)

    def test_last_boundary_rounds_up_not_to_nearest(self):
        """
        The final boundary must round UP (not to nearest) so the video is
        never shorter than the audio it will be muxed with, even when the
        remaining fractional frame is small.
        """
        # 1.0001 frames' worth of total duration at 30fps: nearest-rounding
        # would give 1 frame short of covering the audio; ceil must give 2.
        counts = _cumulative_frame_counts([1.0001 / FPS], FPS)
        assert counts == [2]
