"""Hermes-like local runtime adapter proof-of-concept."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ..dispatcher import write_action
from ..schemas import CittaAction, CittaEvent, action_from_dict, event_from_dict
from ..storage import read_jsonl
from .base import CittaAdapter


class HermesAdapter(CittaAdapter):
    """Map local Hermes-like runtime files into Citta records.

    This proof-of-concept reads files from a local folder only. It does not call
    Hermes APIs or execute runtime commands.
    """

    name = "hermes"

    def __init__(self, runtime_path: str | Path = "examples/hermes_like_runtime/runtime") -> None:
        self.runtime_path = Path(runtime_path)
        self.events_path = self.runtime_path / "events.jsonl"
        self.actions_path = self.runtime_path / "actions.jsonl"
        self.state_path = self.runtime_path / "state.json"
        self.tasks_path = self.runtime_path / "tasks"

    def read_events(self) -> list[CittaEvent]:
        events: list[CittaEvent] = []
        for record in read_jsonl(self.events_path):
            try:
                events.append(event_from_dict(_map_hermes_event(record)))
            except ValueError:
                continue
        return events

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
            "kind": "hermes_like_runtime",
            "runtime_path": str(self.runtime_path),
            "events_path": str(self.events_path),
            "actions_path": str(self.actions_path),
            "state_path": str(self.state_path),
            "tasks_path": str(self.tasks_path),
        }


def _map_hermes_event(record: dict[str, Any]) -> dict[str, Any]:
    metadata = dict(record.get("metadata") or {})
    if "hermes_state" in record:
        metadata["hermes_state"] = record["hermes_state"]
    return {
        "time": record.get("time") or record.get("timestamp"),
        "event_id": record.get("event_id") or record.get("id"),
        "task_id": record.get("task_id") or record.get("task") or "default",
        "agent": record.get("agent") or record.get("worker") or "hermes_agent",
        "framework": "hermes",
        "action": record.get("action") or record.get("type") or "runtime_event",
        "target": record.get("target") or record.get("resource"),
        "status": record.get("status") or "completed",
        "input": record.get("input"),
        "output": record.get("output") or record.get("message"),
        "error": record.get("error"),
        "metadata": metadata,
    }
