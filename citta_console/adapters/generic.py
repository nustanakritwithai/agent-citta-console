"""Generic JSONL adapter for the MVP."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ..dispatcher import dispatch_action
from ..observer import observe
from ..renderer import render_dashboard
from ..trace_reader import read_trace


class GenericJsonlAdapter:
    """Adapter for runtimes that can read and write Citta JSONL files."""

    def __init__(
        self,
        trace_path: str | Path,
        actions_path: str | Path,
        dashboard_path: str | Path = "dashboard.html",
    ) -> None:
        self.trace_path = Path(trace_path)
        self.actions_path = Path(actions_path)
        self.dashboard_path = Path(dashboard_path)

    def read_events(self) -> list[Any]:
        return read_trace(self.trace_path)

    def build_report(self, task_id: str | None = None, goal: str | None = None) -> dict[str, Any]:
        return observe(
            self.trace_path,
            task_id=task_id,
            goal=goal,
            actions_path=self.actions_path,
        )

    def render(self, task_id: str | None = None, goal: str | None = None) -> Path:
        report = self.build_report(task_id=task_id, goal=goal)
        return render_dashboard(report, self.dashboard_path)

    def dispatch(self, action: dict[str, Any], *, confirm: bool = False) -> dict[str, Any]:
        return dispatch_action(action, self.actions_path, confirm=confirm)
