from pathlib import Path

import pytest

from citta_console.dispatcher import (
    cancel_action,
    confirm_action,
    dispatch_action,
    prepare_action,
    read_actions,
)
from citta_console.storage import read_jsonl


def test_dispatch_action_writes_confirmed_safe_action(tmp_path: Path) -> None:
    actions_path = tmp_path / "actions.jsonl"

    record = dispatch_action(
        {"action": "inspect_error", "reason": "Test failed."},
        actions_path,
        task_id="task_1",
    )

    assert record["task_id"] == "task_1"
    assert record["action"] == "inspect_error"
    assert record["status"] == "confirmed"
    assert read_jsonl(actions_path)[0]["reason"] == "Test failed."


def test_prepare_action_requires_reason() -> None:
    with pytest.raises(ValueError):
        prepare_action({"action": "continue"})


def test_medium_action_records_pending_confirmation(tmp_path: Path) -> None:
    record = dispatch_action(
        {"action": "run_tests", "reason": "Need validation."},
        tmp_path / "actions.jsonl",
        task_id="task_1",
    )

    assert record["permission_level"] == "medium"
    assert record["status"] == "pending_confirmation"


def test_dangerous_action_records_pending_confirmation(tmp_path: Path) -> None:
    record = dispatch_action(
        {"action": "run_shell_command", "reason": "Need shell.", "target": "echo ok"},
        tmp_path / "actions.jsonl",
        task_id="task_1",
    )

    assert record["permission_level"] == "dangerous"
    assert record["status"] == "pending_confirmation"


def test_dangerous_action_writes_confirmed_record_when_confirmed(tmp_path: Path) -> None:
    record = dispatch_action(
        {"action": "run_shell_command", "reason": "Need shell.", "target": "echo ok"},
        tmp_path / "actions.jsonl",
        task_id="task_1",
        confirm=True,
    )

    assert record["permission_level"] == "dangerous"
    assert record["status"] == "confirmed"


def test_forbidden_action_is_blocked_and_logged(tmp_path: Path) -> None:
    record = dispatch_action(
        {"action": "delete_project", "reason": "Unsafe request."},
        tmp_path / "actions.jsonl",
        task_id="task_1",
    )

    assert record["permission_level"] == "forbidden"
    assert record["status"] == "blocked"
    assert "Blocked forbidden action" in record["reason"]


def test_read_actions_filters_by_task_and_limit(tmp_path: Path) -> None:
    path = tmp_path / "actions.jsonl"
    dispatch_action({"action": "inspect_error", "reason": "a"}, path, task_id="task_1")
    dispatch_action({"action": "inspect_error", "reason": "b"}, path, task_id="task_2")
    dispatch_action({"action": "inspect_error", "reason": "c"}, path, task_id="task_1")

    actions = read_actions(path, limit=1, task_id="task_1")

    assert len(actions) == 1
    assert actions[0]["reason"] == "c"


def test_confirm_and_cancel_append_audit_records(tmp_path: Path) -> None:
    path = tmp_path / "actions.jsonl"
    pending = dispatch_action({"action": "run_tests", "reason": "Need tests."}, path, task_id="task_1")

    confirmed = confirm_action(path, pending["action_id"])
    cancelled = cancel_action(path, pending["action_id"])

    assert confirmed["status"] == "confirmed"
    assert confirmed["params"]["confirmed_action_id"] == pending["action_id"]
    assert cancelled["status"] == "blocked"
    assert cancelled["params"]["cancelled_action_id"] == pending["action_id"]
