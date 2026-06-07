"""Adapter contract for translating agent runtimes into Citta records."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from ..schemas import CittaAction, CittaEvent


class CittaAdapter(ABC):
    """Minimal dependency-free adapter interface.

    Adapters translate local runtime files, transcripts, or traces into Citta
    events/actions. They must not execute runtime actions directly.
    """

    name: str

    @abstractmethod
    def read_events(self) -> list[CittaEvent]:
        """Return observed Citta events from the adapter source."""

    @abstractmethod
    def read_actions(self) -> list[CittaAction]:
        """Return Citta actions recorded for this adapter source."""

    @abstractmethod
    def write_action(self, action: CittaAction) -> None:
        """Record a Citta action without executing it."""

    @abstractmethod
    def describe_source(self) -> dict[str, Any]:
        """Return a serializable description of the adapter source."""
