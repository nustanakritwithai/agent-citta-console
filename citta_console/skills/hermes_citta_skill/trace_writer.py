"""Helpers for writing Citta-compatible traces from Hermes-style activity."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from citta_console.schemas import now_iso, validate_event


def _merge_metadata(defaults: dict[str, Any], metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    """Return default metadata safely overlaid with caller-provided metadata."""

    merged = dict(defaults)
    if metadata:
        merged.update(metadata)
    return merged


def append_citta_event(
    trace_path: str | Path,
    *,
    task_id: str,
    action: str,
    agent: str = "hermes",
    framework: str = "hermes",
    target: str | None = None,
    status: str = "completed",
    input: str | None = None,
    output: str | None = None,
    error: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Append one Citta event JSON object to a JSONL trace."""

    path = Path(trace_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    event = {
        "time": now_iso(),
        "event_id": _next_event_id(path),
        "task_id": task_id,
        "agent": agent,
        "framework": framework,
        "action": action,
        "target": target,
        "status": status,
        "input": input,
        "output": output,
        "error": error,
        "metadata": metadata or {},
    }
    validate_event(event)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")
    return event


def record_user_input(
    trace_path: str | Path,
    task_id: str,
    content: str,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return append_citta_event(
        trace_path,
        task_id=task_id,
        agent="user",
        action="user_input",
        status="completed",
        input=content,
        output="User request recorded",
        metadata=_merge_metadata({"source": "hermes_citta_skill"}, metadata),
    )


def record_tool_call(
    trace_path: str | Path,
    task_id: str,
    tool: str,
    target: str | None = None,
    status: str = "completed",
    output: str | None = None,
    error: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return append_citta_event(
        trace_path,
        task_id=task_id,
        action=tool,
        target=target,
        status=status,
        output=output,
        error=error,
        metadata=_merge_metadata({"tool": tool, "source": "hermes_citta_skill"}, metadata),
    )


def record_file_edit(
    trace_path: str | Path,
    task_id: str,
    target: str,
    output: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return append_citta_event(
        trace_path,
        task_id=task_id,
        action="edit_file",
        target=target,
        status="completed",
        output=output,
        metadata=_merge_metadata(
            {"files_changed": [target], "source": "hermes_citta_skill"}, metadata
        ),
    )


def record_test_result(
    trace_path: str | Path,
    task_id: str,
    command: str,
    status: str,
    output: str | None = None,
    error: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return append_citta_event(
        trace_path,
        task_id=task_id,
        agent="test_agent",
        action="run_tests",
        target=command,
        status=status,
        input=f"Run {command}",
        output=output,
        error=error,
        metadata=_merge_metadata({"command": command, "source": "hermes_citta_skill"}, metadata),
    )


def record_final_answer(
    trace_path: str | Path,
    task_id: str,
    content: str,
    status: str = "completed",
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return append_citta_event(
        trace_path,
        task_id=task_id,
        action="final_answer",
        status=status,
        output=content,
        metadata=_merge_metadata({"source": "hermes_citta_skill"}, metadata),
    )


def _next_event_id(path: Path) -> str:
    if not path.exists():
        return "evt_001"
    count = 0
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                count += 1
    return f"evt_{count + 1:03d}"
