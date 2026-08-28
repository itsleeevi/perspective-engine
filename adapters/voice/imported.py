"""Imported operator voice-over. The engine never calls a TTS API."""

from __future__ import annotations

from pathlib import Path

from adapters.voice.base import VoiceAdapter, VoiceoverResult
from channel.pauses import load_timestamps
from graph.assets import save_asset


class ImportedVoiceAdapter(VoiceAdapter):
    """Return the operator wav and pause-table beat durations. No synthesis."""

    def __init__(self, audio_path: Path, timestamps_path: Path | None = None) -> None:
        self.audio_path = Path(audio_path)
        self.timestamps_path = Path(timestamps_path) if timestamps_path else None

    async def synthesize(
        self,
        script_beats: list[str],
        shot_durations: list[float],
        voice_id: str = "default",
    ) -> VoiceoverResult:
        if not self.audio_path.is_file():
            raise FileNotFoundError(f"imported voiceover missing: {self.audio_path}")
        url = save_asset(f"voice/{self.audio_path.name}", self.audio_path.read_bytes())
        durations: list[float] = []
        total = 0.0
        if self.timestamps_path and self.timestamps_path.is_file():
            table = load_timestamps(self.timestamps_path)
            rows = list(table.get("scenes") or [])
            durations = [round(float(r["end"]) - float(r["start"]), 3) for r in rows]
            total = float(table.get("duration_seconds") or sum(durations))
            if durations and abs(sum(durations) - total) > 0.05:
                durations[-1] = round(durations[-1] + (total - sum(durations)), 3)
        if not durations:
            durations = [round(float(d), 3) for d in shot_durations]
            total = round(sum(durations), 3)
        if script_beats and durations and len(durations) != len(script_beats):
            # Title-card silent beats are not in an imported VO. Pad/trim to the
            # still count the assembler asked for only when timestamps match.
            if len(durations) < len(script_beats):
                durations = durations + [0.0] * (len(script_beats) - len(durations))
            else:
                durations = durations[: len(script_beats)]
        return VoiceoverResult(
            audio_url=url,
            duration_seconds=round(total or sum(durations), 3),
            beat_durations=durations,
            cost_usd=0.0,
        )
