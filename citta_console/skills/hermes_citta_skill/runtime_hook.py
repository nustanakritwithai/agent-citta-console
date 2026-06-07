"""Opt-in Hermes runtime trace hook.

This helper only writes Citta-compatible JSONL events when explicitly enabled.
It does not execute recommended actions, shell commands, deploys, git pushes,
deletions, or external API calls.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .trace_writer import append_citta_event

PRESERVED_METADATA_KEYS = (
    "confidence",
    "goal_alignment",
    "reason",
    "inspected_error",
    "source_state",
    "risk_hint",
    "notes",
)

_TEST_COMMAND_HINTS = ("pytest", "unittest", "nose", "tox", "coverage", " test", "tests")


class HermesRuntimeTraceHook:
    """Opt-in helper for capturing Hermes-style runtime events as Citta JSONL."""

    def __init__(
        self,
        trace_path: str | Path,
        *,
        enabled: bool = False,
        default_task_id: str | None = None,
        default_metadata: dict[str, Any] | None = None,
    ) -> None:
        self.trace_path = Path(trace_path)
        self.enabled = bool(enabled)
        self.default_task_id = default_task_id
        self.default_metadata = dict(default_metadata or {})

    def is_enabled(self) -> bool:
        """Return whether this hook is allowed to write trace events."""

        return self.enabled

    def record_user_input(
        self,
        content: str,
        *,
        task_id: str | None = None,
        metadata: dict[str, Any] | None = None,
        **caller_metadata: Any,
    ) -> dict[str, Any] | None:
        return self._record(
            task_id=task_id,
            agent="user",
            action="user_input",
            status="completed",
            input=content,
            output="User request recorded",
            event_metadata={"event_type": "user_input"},
            caller_metadata=metadata,
            extra_metadata=caller_metadata,
        )

    def record_tool_call(
        self,
        tool_name: str,
        *,
        target: str | None = None,
        status: str = "completed",
        output: str | None = None,
        error: str | None = None,
        task_id: str | None = None,
        metadata: dict[str, Any] | None = None,
        **caller_metadata: Any,
    ) -> dict[str, Any] | None:
        return self._record(
            task_id=task_id,
            action=tool_name,
            target=target,
            status=status,
            output=output,
            error=error,
            event_metadata={"event_type": "tool_call", "tool": tool_name},
            caller_metadata=metadata,
            extra_metadata=caller_metadata,
        )

    def record_file_edit(
        self,
        path: str,
        *,
        output: str | None = None,
        task_id: str | None = None,
        metadata: dict[str, Any] | None = None,
        **caller_metadata: Any,
    ) -> dict[str, Any] | None:
        return self._record(
            task_id=task_id,
            action="edit_file",
            target=path,
            status="completed",
            output=output,
            event_metadata={"event_type": "file_edit", "files_changed": [path]},
            caller_metadata=metadata,
            extra_metadata=caller_metadata,
        )

    def record_command_result(
        self,
        command: str,
        *,
        status: str = "completed",
        output: str | None = None,
        error: str | None = None,
        task_id: str | None = None,
        metadata: dict[str, Any] | None = None,
        **caller_metadata: Any,
    ) -> dict[str, Any] | None:
        action = "run_tests" if _looks_like_test_command(command) else "command_result"
        agent = "test_agent" if action == "run_tests" else "hermes"
        return self._record(
            task_id=task_id,
            agent=agent,
            action=action,
            target=command,
            status=status,
            input=f"Run {command}",
            output=output,
            error=error,
            event_metadata={"event_type": "command_result", "command": command},
            caller_metadata=metadata,
            extra_metadata=caller_metadata,
        )

    def record_error(
        self,
        error: str,
        *,
        target: str | None = None,
        task_id: str | None = None,
        metadata: dict[str, Any] | None = None,
        **caller_metadata: Any,
    ) -> dict[str, Any] | None:
        return self._record(
            task_id=task_id,
            action="error",
            target=target,
            status="failed",
            error=error,
            event_metadata={"event_type": "error"},
            caller_metadata=metadata,
            extra_metadata=caller_metadata,
        )

    def record_final_answer(
        self,
        content: str,
        *,
        status: str = "completed",
        task_id: str | None = None,
        metadata: dict[str, Any] | None = None,
        **caller_metadata: Any,
    ) -> dict[str, Any] | None:
        return self._record(
            task_id=task_id,
            action="final_answer",
            status=status,
            output=content,
            event_metadata={"event_type": "final_answer"},
            caller_metadata=metadata,
            extra_metadata=caller_metadata,
        )

    def record_vipaka_check(
        self,
        result: str,
        *,
        status: str = "completed",
        target: str | None = None,
        task_id: str | None = None,
        metadata: dict[str, Any] | None = None,
        **caller_metadata: Any,
    ) -> dict[str, Any] | None:
        return self._record(
            task_id=task_id,
            action="vipaka_check",
            target=target,
            status=status,
            output=result,
            event_metadata={"event_type": "vipaka_check"},
            caller_metadata=metadata,
            extra_metadata=caller_metadata,
        )

    def _record(
        self,
        *,
        task_id: str | None,
        action: str,
        status: str,
        agent: str = "hermes",
        target: str | None = None,
        input: str | None = None,
        output: str | None = None,
        error: str | None = None,
        event_metadata: dict[str, Any] | None = None,
        caller_metadata: dict[str, Any] | None = None,
        extra_metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        if not self.enabled:
            return None
        active_task_id = task_id or self.default_task_id
        if not active_task_id:
            raise ValueError("task_id is required when default_task_id is not set")
        metadata = self._merge_metadata(event_metadata, caller_metadata, extra_metadata)
        return append_citta_event(
            self.trace_path,
            task_id=active_task_id,
            agent=agent,
            framework="hermes",
            action=action,
            target=target,
            status=status,
            input=input,
            output=output,
            error=error,
            metadata=metadata,
        )

    def _merge_metadata(
        self,
        event_metadata: dict[str, Any] | None,
        caller_metadata: dict[str, Any] | None,
        extra_metadata: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """Merge metadata safely: defaults < event metadata < caller metadata."""

        merged: dict[str, Any] = {"source": "hermes_runtime_trace_hook"}
        merged.update(self.default_metadata)
        if event_metadata:
            merged.update(event_metadata)
        if caller_metadata:
            merged.update(caller_metadata)
        if extra_metadata:
            merged.update({key: value for key, value in extra_metadata.items() if value is not None})
        return merged


def _looks_like_test_command(command: str) -> bool:
    normalized = f" {command.lower()} "
    return any(hint in normalized for hint in _TEST_COMMAND_HINTS)
