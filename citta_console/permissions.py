"""Permission model for action dispatch."""

from __future__ import annotations

from typing import Mapping

from .schemas import PermissionLevel

SAFE_ACTIONS = {
    "view_trace",
    "view_diff",
    "summarize_state",
    "inspect_error",
    "read_file",
    "show_logs",
    "continue",
}

MEDIUM_ACTIONS = {
    "run_tests",
    "create_file",
    "edit_draft",
    "redirect",
    "redirect_task",
    "pause",
    "pause_agent",
    "ask_user",
    "approve",
    "reject",
    "rollback",
}

DANGEROUS_ACTIONS = {
    "delete_file",
    "overwrite_file",
    "run_shell_command",
    "install_package",
    "git_push",
    "deploy",
    "modify_many_files",
    "stop",
}

FORBIDDEN_ACTIONS = {
    "delete_project",
    "send_email",
    "publish_content",
    "deploy_production",
    "wipe_memory",
}


def classify_action(action_name: str) -> str:
    name = action_name.strip().lower()
    if name in FORBIDDEN_ACTIONS:
        return PermissionLevel.FORBIDDEN.value
    if name in DANGEROUS_ACTIONS:
        return PermissionLevel.DANGEROUS.value
    if name in MEDIUM_ACTIONS:
        return PermissionLevel.MEDIUM.value
    return PermissionLevel.SAFE.value


def validate_permission(action: Mapping[str, object], confirm: bool = False) -> str:
    """Return the effective permission level or raise for blocked actions."""

    action_name = str(action.get("action", ""))
    level = str(action.get("permission_level") or classify_action(action_name))
    classified = classify_action(action_name)
    if classified == PermissionLevel.FORBIDDEN.value:
        raise PermissionError(f"action '{action_name}' is forbidden by default")
    if classified == PermissionLevel.DANGEROUS.value:
        level = classified
    if level == PermissionLevel.DANGEROUS.value and not confirm:
        raise PermissionError(f"dangerous action '{action_name}' requires confirmation")
    return level
