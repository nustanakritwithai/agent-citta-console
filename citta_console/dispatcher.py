"""Dispatch selected Citta actions.

The MVP dispatcher only appends actions to JSONL. Runtime-specific adapters can
watch that file and decide how to execute the intention.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from .permissions import classify_action, validate_permission
from .schemas import CittaAction, action_from_dict, make_id, now_iso


def prepare_action(action: Mapping[str, Any], task_id: str | None = None) -> CittaAction:
    action_name = str(action.get("action", "")).strip()
    if not action_name:
        raise ValueError("action is required")
    reason = str(action.get("reason", "")).strip()
    if not reason:
        raise ValueError("reason is required")

    payload = dict(action)
    payload.setdefault("time", now_iso())
    payload.setdefault("action_id", make_id("act"))
    payload["task_id"] = str(payload.get("task_id") or task_id or "default")
    payload["action"] = action_name
    payload["reason"] = reason
    payload.setdefault("permission_level", classify_action(action_name))
    payload.setdefault("params", {})
    return action_from_dict(payload)


def write_action(path: str | Path, action: Mapping[str, Any] | CittaAction) -> dict[str, Any]:
    action_obj = action if isinstance(action, CittaAction) else action_from_dict(action)
    action_path = Path(path)
    action_path.parent.mkdir(parents=True, exist_ok=True)
    record = action_obj.to_dict()
    with action_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
    return record


def dispatch_action(
    action: Mapping[str, Any],
    path: str | Path = "actions.jsonl",
    *,
    task_id: str | None = None,
    confirm: bool = False,
) -> dict[str, Any]:
    prepared = prepare_action(action, task_id=task_id)
    level = validate_permission(prepared.to_dict(), confirm=confirm)
    prepared.permission_level = level
    return write_action(path, prepared)
