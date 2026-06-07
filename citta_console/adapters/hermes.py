"""Placeholder Hermes adapter.

The v0.1 core is framework-agnostic. This module documents the intended adapter
boundary without depending on a Hermes runtime layout yet.
"""

from __future__ import annotations

from pathlib import Path


class HermesAdapter:
    def __init__(self, runtime_path: str | Path) -> None:
        self.runtime_path = Path(runtime_path)

    def to_citta_events(self) -> list[dict[str, object]]:
        raise NotImplementedError("Hermes integration is planned after the generic MVP.")
