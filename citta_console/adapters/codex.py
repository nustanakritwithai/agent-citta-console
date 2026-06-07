"""Placeholder Codex transcript adapter."""

from __future__ import annotations

from pathlib import Path


class CodexTranscriptAdapter:
    def __init__(self, transcript_path: str | Path) -> None:
        self.transcript_path = Path(transcript_path)

    def to_citta_events(self) -> list[dict[str, object]]:
        raise NotImplementedError("Codex transcript parsing is planned after the generic MVP.")
