"""OpenClaw adapter stub.

The v0.3 foundation exposes the adapter contract without implementing a real
OpenClaw integration yet.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ..dispatcher import write_action
from ..schemas import CittaAction, CittaEvent, action_from_dict
from ..storage import read_jsonl
from .base import CittaAdapter


class OpenClawAdapter(CittaAdapter):
    name = "openclaw"

    def __init__(
        self,
        workspace_path: str | Path = "examples/openclaw_workspace",
        actions_path: str | Path | None = None,
    ) -> None:
        self.workspace_path = Path(workspace_path)
        self.actions_path = Path(actions_path) if actions_path else self.workspace_path / "actions.jsonl"

    def read_events(self) -> list[CittaEvent]:
        return []

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
            "kind": "stub",
            "workspace_path": str(self.workspace_path),
            "actions_path": str(self.actions_path),
        }
