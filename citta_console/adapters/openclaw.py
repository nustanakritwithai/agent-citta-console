"""Placeholder OpenClaw adapter."""

from __future__ import annotations

from pathlib import Path


class OpenClawAdapter:
    def __init__(self, workspace_path: str | Path) -> None:
        self.workspace_path = Path(workspace_path)

    def to_citta_events(self) -> list[dict[str, object]]:
        raise NotImplementedError("OpenClaw integration is planned after the generic MVP.")
