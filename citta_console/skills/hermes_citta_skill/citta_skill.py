"""Experimental Hermes Citta Skill wrapper."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from citta_console.observer import observe
from citta_console.renderer import render_dashboard

from .trace_writer import (
    record_file_edit,
    record_final_answer,
    record_test_result,
    record_tool_call,
    record_user_input,
)


class HermesCittaSkill:
    """Local skill wrapper for writing traces and rendering Citta dashboards."""

    def __init__(
        self,
        trace_path: str | Path,
        actions_path: str | Path,
        dashboard_path: str | Path,
    ) -> None:
        self.trace_path = Path(trace_path)
        self.actions_path = Path(actions_path)
        self.dashboard_path = Path(dashboard_path)
        self.actions_path.parent.mkdir(parents=True, exist_ok=True)
        self.actions_path.touch(exist_ok=True)

    def record_user_input(self, task_id: str, content: str) -> dict[str, Any]:
        return record_user_input(self.trace_path, task_id, content)

    def record_tool_call(
        self,
        task_id: str,
        tool: str,
        target: str | None = None,
        status: str = "completed",
        output: str | None = None,
        error: str | None = None,
    ) -> dict[str, Any]:
        return record_tool_call(
            self.trace_path,
            task_id,
            tool,
            target=target,
            status=status,
            output=output,
            error=error,
        )

    def record_file_edit(
        self,
        task_id: str,
        target: str,
        output: str | None = None,
    ) -> dict[str, Any]:
        return record_file_edit(self.trace_path, task_id, target, output=output)

    def record_test_result(
        self,
        task_id: str,
        command: str,
        status: str,
        output: str | None = None,
        error: str | None = None,
    ) -> dict[str, Any]:
        return record_test_result(
            self.trace_path,
            task_id,
            command,
            status,
            output=output,
            error=error,
        )

    def record_final_answer(
        self,
        task_id: str,
        content: str,
        status: str = "completed",
    ) -> dict[str, Any]:
        return record_final_answer(self.trace_path, task_id, content, status=status)

    def observe(self, goal: str | None = None, task_id: str | None = None) -> dict[str, Any]:
        report = observe(
            self.trace_path,
            actions_path=self.actions_path,
            goal=goal,
            task_id=task_id,
        )
        render_dashboard(report, self.dashboard_path)
        return report
