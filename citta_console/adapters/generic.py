"""Generic JSONL adapter."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ..config import CittaConfig, default_config
from ..dispatcher import dispatch_action, read_actions, write_action
from ..observer import observe
from ..renderer import render_dashboard
from ..schemas import CittaAction, action_from_dict
from ..trace_reader import read_trace
from .base import CittaAdapter


class GenericJsonlAdapter(CittaAdapter):
    """Adapter for runtimes that read and write Citta JSONL files."""

    name = "generic"

    def __init__(
        self,
        trace_path: str | Path | None = None,
        actions_path: str | Path | None = None,
        dashboard_path: str | Path | None = None,
        config: CittaConfig | dict[str, Any] | None = None,
    ) -> None:
        active_config = _coerce_config(config)
        self.trace_path = Path(trace_path or active_config.trace_path)
        self.actions_path = Path(actions_path or active_config.actions_path)
        self.dashboard_path = Path(dashboard_path or active_config.dashboard_path)
        self.config = active_config

    def read_events(self) -> list[Any]:
        return read_trace(self.trace_path)

    def read_actions(self) -> list[CittaAction]:
        return [action_from_dict(action) for action in read_actions(self.actions_path, limit=100)]

    def write_action(self, action: CittaAction) -> None:
        write_action(self.actions_path, action)

    def describe_source(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "kind": "jsonl",
            "trace_path": str(self.trace_path),
            "actions_path": str(self.actions_path),
            "dashboard_path": str(self.dashboard_path),
        }

    def build_report(self, task_id: str | None = None, goal: str | None = None) -> dict[str, Any]:
        return observe(
            self.trace_path,
            task_id=task_id,
            goal=goal if goal is not None else self.config.goal,
            actions_path=self.actions_path,
        )

    def render(self, task_id: str | None = None, goal: str | None = None) -> Path:
        report = self.build_report(task_id=task_id, goal=goal)
        return render_dashboard(
            report,
            self.dashboard_path,
            refresh_interval_seconds=self.config.refresh_interval_seconds,
        )

    def dispatch(self, action: dict[str, Any], *, confirm: bool = False) -> dict[str, Any]:
        return dispatch_action(
            action,
            self.actions_path,
            confirm=confirm,
            require_confirmation_for_medium=self.config.require_confirmation_for_medium,
            require_confirmation_for_dangerous=self.config.require_confirmation_for_dangerous,
            block_forbidden_actions=self.config.block_forbidden_actions,
        )


def _coerce_config(config: CittaConfig | dict[str, Any] | None) -> CittaConfig:
    if config is None:
        return default_config()
    if isinstance(config, CittaConfig):
        return config
    merged = default_config().to_dict()
    merged.update(config)
    return CittaConfig(**merged)
