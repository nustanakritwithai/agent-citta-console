"""Read Citta JSONL traces."""

from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from .schemas import CittaEvent, event_from_dict, to_dict


def _coerce_event(value: CittaEvent | dict[str, Any]) -> CittaEvent:
    if isinstance(value, CittaEvent):
        return value
    return event_from_dict(value)


def read_trace(path: str | Path) -> list[CittaEvent]:
    """Read valid events from a JSONL trace file.

    Missing files and malformed lines are skipped. This keeps the console usable
    while a body agent is actively appending to the trace.
    """

    trace_path = Path(path)
    if not trace_path.exists():
        return []

    events: list[CittaEvent] = []
    with trace_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if not stripped:
                continue
            try:
                payload = json.loads(stripped)
                events.append(event_from_dict(payload))
            except (json.JSONDecodeError, TypeError, ValueError):
                continue
    return events


def read_recent_events(path: str | Path, limit: int = 20) -> list[CittaEvent]:
    if limit <= 0:
        return []
    return read_trace(path)[-limit:]


def filter_events_by_task(
    events: Iterable[CittaEvent | dict[str, Any]], task_id: str
) -> list[CittaEvent]:
    return [event for event in map(_coerce_event, events) if event.task_id == task_id]


def filter_events_by_status(
    events: Iterable[CittaEvent | dict[str, Any]], status: str
) -> list[CittaEvent]:
    return [event for event in map(_coerce_event, events) if event.status == status]


def get_active_agents(events: Iterable[CittaEvent | dict[str, Any]]) -> list[str]:
    """Return agents with running/pending work, or recent agents as a fallback."""

    coerced = [_coerce_event(event) for event in events]
    active: list[str] = []
    for event in coerced:
        if event.status in {"pending", "running", "blocked"} and event.agent not in active:
            active.append(event.agent)
    if active:
        return active

    recent_agents: list[str] = []
    for event in coerced[-20:]:
        if event.agent not in recent_agents:
            recent_agents.append(event.agent)
    return recent_agents


def events_to_dicts(events: Iterable[CittaEvent | dict[str, Any]]) -> list[dict[str, Any]]:
    return [to_dict(event) for event in events]
