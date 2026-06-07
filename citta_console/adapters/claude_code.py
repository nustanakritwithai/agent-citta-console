"""Local Claude Code transcript mock adapter."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ..dispatcher import write_action
from ..schemas import CittaAction, CittaEvent, action_from_dict
from ..storage import read_jsonl
from .base import CittaAdapter
from .codex import _read_transcript_events


class ClaudeCodeTranscriptAdapter(CittaAdapter):
    """Parse local Claude Code-like transcript fixtures into Citta events."""

    name = "claude_code"

    def __init__(
        self,
        transcript_path: str | Path = "examples/transcripts/claude_code_transcript.jsonl",
        actions_path: str | Path | None = None,
    ) -> None:
        self.transcript_path = Path(transcript_path)
        self.actions_path = Path(actions_path) if actions_path else self.transcript_path.with_suffix(".actions.jsonl")

    def read_events(self) -> list[CittaEvent]:
        return _read_transcript_events(
            self.transcript_path,
            framework="claude_code",
            agent="claude_code_agent",
        )

    def read_actions(self) -> list[CittaAction]:
        actions: list[CittaAction] = []
        for record in read_jsonl(self.actions_path):
            try:
                actions.append(action_from_dict(record))
            except ValueError:
                continue
        return actions

    def write_action(self, action: CittaAction) -> None:
        write_action(self.actions_path, action)

    def describe_source(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "kind": "transcript",
            "transcript_path": str(self.transcript_path),
            "actions_path": str(self.actions_path),
        }


ClaudeCodeAdapter = ClaudeCodeTranscriptAdapter
