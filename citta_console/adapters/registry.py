"""Adapter registry for built-in and custom Citta adapters."""

from __future__ import annotations

from typing import Any, Type

from .base import CittaAdapter
from .claude_code import ClaudeCodeTranscriptAdapter
from .codex import CodexTranscriptAdapter
from .generic import GenericJsonlAdapter
from .hermes import HermesAdapter
from .openclaw import OpenClawAdapter


_ADAPTERS: dict[str, Type[CittaAdapter]] = {
    "generic": GenericJsonlAdapter,
    "hermes": HermesAdapter,
    "openclaw": OpenClawAdapter,
    "codex": CodexTranscriptAdapter,
    "claude_code": ClaudeCodeTranscriptAdapter,
}


def register_adapter(name: str, adapter_cls: Type[CittaAdapter]) -> None:
    if not name:
        raise ValueError("adapter name is required")
    _ADAPTERS[name] = adapter_cls


def list_adapters() -> list[str]:
    return sorted(_ADAPTERS)


def get_adapter(name: str, config: Any = None) -> CittaAdapter:
    try:
        adapter_cls = _ADAPTERS[name]
    except KeyError as exc:
        raise ValueError(f"unknown adapter: {name}") from exc
    if config is None:
        return adapter_cls()
    if isinstance(config, dict):
        return adapter_cls(**config)
    return adapter_cls(config=config)
