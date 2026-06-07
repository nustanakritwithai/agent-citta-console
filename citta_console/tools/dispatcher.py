"""Local tool dispatcher for Citta MCP-style calls."""

from __future__ import annotations

from typing import Any

from .definitions import get_tool_definition, list_tool_definitions


def dispatch_tool(name: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    if payload is None:
        payload = {}
    if not isinstance(payload, dict):
        return {"ok": False, "error": "tool input must be a JSON object"}
    try:
        definition = get_tool_definition(name)
        return definition.handler(payload)
    except Exception as exc:  # Local tool boundary returns JSON errors to callers.
        return {"ok": False, "error": str(exc), "tool": name}


def require_tool_success(name: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    result = dispatch_tool(name, payload)
    if not result.get("ok"):
        raise RuntimeError(str(result.get("error", "tool call failed")))
    return result


__all__ = ["dispatch_tool", "list_tool_definitions", "require_tool_success"]
