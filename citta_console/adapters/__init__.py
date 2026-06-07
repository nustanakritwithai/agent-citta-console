"""Runtime adapters translate external agent traces into Citta events."""

from .base import CittaAdapter
from .claude_code import ClaudeCodeTranscriptAdapter
from .codex import CodexTranscriptAdapter
from .generic import GenericJsonlAdapter
from .hermes import HermesAdapter
from .openclaw import OpenClawAdapter
from .registry import get_adapter, list_adapters, register_adapter

__all__ = [
    "CittaAdapter",
    "ClaudeCodeTranscriptAdapter",
    "CodexTranscriptAdapter",
    "GenericJsonlAdapter",
    "HermesAdapter",
    "OpenClawAdapter",
    "get_adapter",
    "list_adapters",
    "register_adapter",
]
