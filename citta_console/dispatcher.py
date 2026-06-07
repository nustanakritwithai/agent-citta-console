"""Dispatch selected Citta actions.

The dispatcher only appends action records to JSONL. It never executes shell
commands, deploys, deletes files, or performs runtime-specific side effects.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from .permissions import classify_action, validate_permission
from .schemas import ActionStatus, CittaAction, PermissionLevel, action_from_dict, make_id, now_iso
from .storage import read_jsonl


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
    payload.setdefault("status", ActionStatus.CONFIRMED.value)
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
    require_confirmation_for_medium: bool = True,
    require_confirmation_for_dangerous: bool = True,
    block_forbidden_actions: bool = True,
) -> dict[str, Any]:
    """Append an action record with confirmation status.

    Safe actions are recorded as confirmed. Medium and dangerous actions are
    recorded as pending confirmation unless `confirm=True` or the relevant
    confirmation requirement is disabled. Forbidden actions are blocked by
    default and still logged for auditability.
    """

    prepared = prepare_action(action, task_id=task_id)
    level = classify_action(prepared.action)
    prepared.permission_level = level

    if level == PermissionLevel.FORBIDDEN.value and block_forbidden_actions:
        prepared.status = ActionStatus.BLOCKED.value
        prepared.reason = f"Blocked forbidden action: {prepared.reason}"
        return write_action(path, prepared)

    needs_confirmation = (
        (level == PermissionLevel.MEDIUM.value and require_confirmation_for_medium)
        or (level == PermissionLevel.DANGEROUS.value and require_confirmation_for_dangerous)
    )
    if needs_confirmation and not confirm:
        prepared.status = ActionStatus.PENDING_CONFIRMATION.value
        return write_action(path, prepared)

    validate_permission(prepared.to_dict(), confirm=confirm)
    prepared.status = ActionStatus.CONFIRMED.value
    return write_action(path, prepared)


def read_actions(
    path: str | Path,
    limit: int = 20,
    *,
    task_id: str | None = None,
) -> list[dict[str, Any]]:
    actions = read_jsonl(path)
    if task_id:
        actions = [action for action in actions if action.get("task_id") == task_id]
    if limit <= 0:
        return []
    return actions[-limit:]


def find_action(path: str | Path, action_id: str) -> dict[str, Any] | None:
    for action in reversed(read_jsonl(path)):
        if action.get("action_id") == action_id:
            return action
    return None


def confirm_action(path: str | Path, action_id: str, reason: str | None = None) -> dict[str, Any]:
    original = find_action(path, action_id)
    if not original:
        raise ValueError(f"action not found: {action_id}")
    if original.get("status") == ActionStatus.BLOCKED.value:
        raise ValueError(f"blocked action cannot be confirmed: {action_id}")

    params = dict(original.get("params") or {})
    params["confirmed_action_id"] = action_id
    record = {
        "task_id": original.get("task_id", "default"),
        "action": original.get("action"),
        "target": original.get("target"),
        "reason": reason or f"Confirmed action {action_id}: {original.get('reason', '')}",
        "permission_level": original.get("permission_level", PermissionLevel.SAFE.value),
        "status": ActionStatus.CONFIRMED.value,
        "params": params,
    }
    return dispatch_action(
        record,
        path,
        confirm=True,
        require_confirmation_for_medium=False,
        require_confirmation_for_dangerous=False,
        block_forbidden_actions=True,
    )


def cancel_action(path: str | Path, action_id: str, reason: str | None = None) -> dict[str, Any]:
    original = find_action(path, action_id)
    if not original:
        raise ValueError(f"action not found: {action_id}")

    params = dict(original.get("params") or {})
    params["cancelled_action_id"] = action_id
    record = {
        "time": now_iso(),
        "action_id": make_id("act"),
        "task_id": original.get("task_id", "default"),
        "action": original.get("action"),
        "target": original.get("target"),
        "reason": reason or f"Cancelled action {action_id}: {original.get('reason', '')}",
        "permission_level": original.get("permission_level", PermissionLevel.SAFE.value),
        "status": ActionStatus.BLOCKED.value,
        "params": params,
    }
    return write_action(path, action_from_dict(record))
