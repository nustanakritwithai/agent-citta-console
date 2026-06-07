"""State analysis for Citta traces."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from typing import Any

from .schemas import CittaEvent, to_dict
from .trace_reader import get_active_agents

EDIT_ACTIONS = {
    "edit_file",
    "write_file",
    "create_file",
    "modify_file",
    "overwrite_file",
    "delete_file",
}

TEST_ACTIONS = {"run_tests", "test", "pytest", "unit_test", "integration_test"}


def _event_dicts(events: Iterable[CittaEvent | dict[str, Any]]) -> list[dict[str, Any]]:
    return [to_dict(event) for event in events]


def _is_edit(event: dict[str, Any]) -> bool:
    action = str(event.get("action", "")).lower()
    return action in EDIT_ACTIONS or action.endswith("_file")


def _is_test(event: dict[str, Any]) -> bool:
    action = str(event.get("action", "")).lower()
    agent = str(event.get("agent", "")).lower()
    target = str(event.get("target", "")).lower()
    return action in TEST_ACTIONS or "test" in action or "test" in agent or "test" in target


def detect_active_agents(events: Iterable[CittaEvent | dict[str, Any]]) -> list[str]:
    return get_active_agents(events)


def summarize_recent_activity(events: Iterable[CittaEvent | dict[str, Any]], limit: int = 5) -> str:
    event_list = _event_dicts(events)[-limit:]
    if not event_list:
        return "No trace events have been recorded yet."

    parts: list[str] = []
    for event in event_list:
        agent = event.get("agent", "agent")
        action = event.get("action", "acted")
        status = event.get("status", "unknown")
        target = event.get("target")
        if target:
            parts.append(f"{agent} {action} on {target} ({status})")
        else:
            parts.append(f"{agent} {action} ({status})")
    return "; ".join(parts) + "."


def detect_task_progress(events: Iterable[CittaEvent | dict[str, Any]]) -> dict[str, Any]:
    event_list = _event_dicts(events)
    statuses = Counter(str(event.get("status", "unknown")) for event in event_list)
    edited_files = [
        event.get("target")
        for event in event_list
        if _is_edit(event) and event.get("target")
    ]
    return {
        "total_events": len(event_list),
        "status_counts": dict(statuses),
        "edited_files": edited_files,
        "last_status": event_list[-1].get("status") if event_list else None,
        "last_action": event_list[-1].get("action") if event_list else None,
    }


def analyze_current_state(
    events: Iterable[CittaEvent | dict[str, Any]], goal: str | None = None
) -> dict[str, Any]:
    event_list = _event_dicts(events)
    if not event_list:
        return {
            "current_state": "no_trace",
            "active_agents": [],
            "summary": "No trace events have been recorded yet.",
            "progress": detect_task_progress([]),
            "goal": goal,
        }

    last = event_list[-1]
    failed_indices = [
        index for index, event in enumerate(event_list) if event.get("status") == "failed"
    ]
    last_failed_index = failed_indices[-1] if failed_indices else None
    edits_after_failure = (
        any(_is_edit(event) for event in event_list[last_failed_index + 1 :])
        if last_failed_index is not None
        else False
    )
    tests_after_last_edit = False
    edit_indices = [index for index, event in enumerate(event_list) if _is_edit(event)]
    if edit_indices:
        tests_after_last_edit = any(_is_test(event) for event in event_list[edit_indices[-1] + 1 :])

    if last.get("status") in {"pending", "running"}:
        current_state = "agent_running"
    elif last.get("status") == "blocked":
        current_state = "agent_blocked"
    elif last.get("status") == "failed" and _is_test(last):
        current_state = "test_failed"
    elif edits_after_failure:
        current_state = "test_failed_after_file_edit"
    elif edit_indices and not tests_after_last_edit:
        current_state = "code_changed_no_test"
    elif last.get("status") == "failed":
        current_state = "event_failed"
    elif last.get("status") == "completed":
        current_state = "latest_action_completed"
    else:
        current_state = "trace_observed"

    return {
        "current_state": current_state,
        "active_agents": detect_active_agents(event_list),
        "summary": summarize_recent_activity(event_list),
        "progress": detect_task_progress(event_list),
        "goal": goal,
    }
