"""Local handlers for Citta tool calls."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ..adapters.registry import get_adapter, list_adapters
from ..config import CittaConfig, load_config
from ..dispatcher import dispatch_action, read_actions
from ..memory import summarize_reflection_history
from ..observer import observe, observe_with_adapter
from ..renderer import render_dashboard
from ..trace_reader import events_to_dicts, read_trace


def handle_observe(payload: dict[str, Any]) -> dict[str, Any]:
    dashboard_path = _required_str(payload, "dashboard_path")
    report = observe(
        _required_str(payload, "trace_path"),
        actions_path=_required_str(payload, "actions_path"),
        goal=payload.get("goal"),
        task_id=payload.get("task_id"),
    )
    render_dashboard(report, dashboard_path)
    return {"ok": True, "report": report, "dashboard_path": dashboard_path}


def handle_render_dashboard(payload: dict[str, Any]) -> dict[str, Any]:
    dashboard_path = _required_str(payload, "dashboard_path")
    report = observe(
        _required_str(payload, "trace_path"),
        actions_path=_required_str(payload, "actions_path"),
        goal=payload.get("goal"),
        task_id=payload.get("task_id"),
    )
    render_dashboard(report, dashboard_path)
    return {"ok": True, "dashboard_path": dashboard_path}


def handle_read_events(payload: dict[str, Any]) -> dict[str, Any]:
    limit = _limit(payload)
    events = events_to_dicts(read_trace(_required_str(payload, "trace_path"))[-limit:])
    return {"ok": True, "events": events}


def handle_read_actions(payload: dict[str, Any]) -> dict[str, Any]:
    actions = read_actions(_required_str(payload, "actions_path"), limit=_limit(payload))
    return {"ok": True, "actions": actions}


def handle_write_action(payload: dict[str, Any]) -> dict[str, Any]:
    action = payload.get("action")
    if not isinstance(action, dict):
        raise ValueError("action must be an object")
    record = dispatch_action(
        action,
        _required_str(payload, "actions_path"),
        confirm=bool(payload.get("confirm", False)),
    )
    return {
        "ok": True,
        "action_id": record["action_id"],
        "status": record.get("status"),
        "record": record,
    }


def handle_list_adapters(payload: dict[str, Any]) -> dict[str, Any]:
    return {"ok": True, "adapters": list_adapters()}


def handle_describe_adapter(payload: dict[str, Any]) -> dict[str, Any]:
    name = _required_str(payload, "adapter")
    adapter = get_adapter(name)
    return {"ok": True, "adapter": name, "description": adapter.describe_source()}


def handle_observe_with_adapter(payload: dict[str, Any]) -> dict[str, Any]:
    name = _required_str(payload, "adapter")
    config = _load_optional_config(payload.get("config_path"))
    adapter = get_adapter(name, config=config) if name == "generic" else get_adapter(name)
    dashboard_path = _required_str(payload, "dashboard_path")
    report = observe_with_adapter(
        adapter,
        dashboard_path=dashboard_path,
        goal=payload.get("goal") if payload.get("goal") is not None else getattr(config, "goal", None),
        task_id=payload.get("task_id"),
        refresh_interval_seconds=getattr(config, "refresh_interval_seconds", 0),
    )
    return {
        "ok": True,
        "adapter": name,
        "report": report,
        "dashboard_path": dashboard_path,
    }


def handle_summarize_reflections(payload: dict[str, Any]) -> dict[str, Any]:
    lesson_limit = payload.get("lesson_limit", 5)
    mistake_limit = payload.get("mistake_limit", 5)
    if not isinstance(lesson_limit, int) or isinstance(lesson_limit, bool) or lesson_limit < 0:
        raise ValueError("lesson_limit must be a non-negative integer")
    if not isinstance(mistake_limit, int) or isinstance(mistake_limit, bool) or mistake_limit < 0:
        raise ValueError("mistake_limit must be a non-negative integer")

    memory = summarize_reflection_history(
        _required_str(payload, "reflections_path"),
        task_id=payload.get("task_id"),
        lesson_limit=lesson_limit,
        mistake_limit=mistake_limit,
    )
    return {"ok": True, "memory": memory}


def _required_str(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"{key} is required")
    return value


def _limit(payload: dict[str, Any]) -> int:
    value = payload.get("limit", 20)
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ValueError("limit must be a non-negative integer")
    return value


def _load_optional_config(path: Any) -> CittaConfig | None:
    if path is None:
        return None
    if not isinstance(path, str) or not path:
        raise ValueError("config_path must be a string when provided")
    return load_config(path)
