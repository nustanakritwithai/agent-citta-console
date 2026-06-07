"""Local Codex transcript mock adapter."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ..dispatcher import write_action
from ..schemas import CittaAction, CittaEvent, action_from_dict, event_from_dict, now_iso
from ..storage import read_jsonl
from .base import CittaAdapter


class CodexTranscriptAdapter(CittaAdapter):
    """Parse local Codex-like transcript fixtures into Citta events."""

    name = "codex"

    def __init__(
        self,
        transcript_path: str | Path = "examples/transcripts/codex_transcript.jsonl",
        actions_path: str | Path | None = None,
    ) -> None:
        self.transcript_path = Path(transcript_path)
        self.actions_path = Path(actions_path) if actions_path else self.transcript_path.with_suffix(".actions.jsonl")

    def read_events(self) -> list[CittaEvent]:
        return _read_transcript_events(self.transcript_path, framework="codex", agent="codex_agent")

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


CodexAdapter = CodexTranscriptAdapter


def _read_transcript_events(path: Path, *, framework: str, agent: str) -> list[CittaEvent]:
    if not path.exists():
        return []
    records = read_jsonl(path)
    if records:
        return [_event for record in records if (_event := _event_from_record(record, framework, agent))]
    return _events_from_text(path, framework=framework, agent=agent)


def _event_from_record(record: dict[str, Any], framework: str, agent: str) -> CittaEvent | None:
    payload = {
        "time": record.get("time") or record.get("timestamp") or now_iso(),
        "event_id": record.get("event_id") or record.get("id"),
        "task_id": record.get("task_id") or record.get("task") or "transcript",
        "agent": record.get("agent") or agent,
        "framework": record.get("framework") or framework,
        "action": record.get("action") or record.get("type") or "transcript_entry",
        "target": record.get("target") or record.get("file") or record.get("command"),
        "status": record.get("status") or ("failed" if record.get("error") else "completed"),
        "output": record.get("output") or record.get("message") or record.get("content"),
        "error": record.get("error"),
        "metadata": {"source": "transcript"},
    }
    try:
        return event_from_dict(payload)
    except ValueError:
        return None


def _events_from_text(path: Path, *, framework: str, agent: str) -> list[CittaEvent]:
    events: list[CittaEvent] = []
    for index, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        events.append(
            event_from_dict(
                {
                    "time": now_iso(),
                    "event_id": f"{framework}_line_{index}",
                    "task_id": "transcript",
                    "agent": agent,
                    "framework": framework,
                    "action": "transcript_line",
                    "status": "completed",
                    "output": stripped,
                    "metadata": {"line": index, "source": str(path)},
                }
            )
        )
    return events
