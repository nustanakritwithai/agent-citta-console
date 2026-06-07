from pathlib import Path

import pytest

from citta_console.dispatcher import dispatch_action, prepare_action
from citta_console.storage import read_jsonl


def test_dispatch_action_writes_jsonl(tmp_path: Path) -> None:
    actions_path = tmp_path / "actions.jsonl"

    record = dispatch_action(
        {"action": "inspect_error", "reason": "Test failed."},
        actions_path,
        task_id="task_1",
    )

    assert record["task_id"] == "task_1"
    assert record["action"] == "inspect_error"
    assert read_jsonl(actions_path)[0]["reason"] == "Test failed."


def test_prepare_action_requires_reason() -> None:
    with pytest.raises(ValueError):
        prepare_action({"action": "continue"})


def test_dangerous_action_requires_confirm(tmp_path: Path) -> None:
    with pytest.raises(PermissionError):
        dispatch_action(
            {"action": "run_shell_command", "reason": "Need shell.", "target": "echo ok"},
            tmp_path / "actions.jsonl",
            task_id="task_1",
        )


def test_dangerous_action_writes_when_confirmed(tmp_path: Path) -> None:
    record = dispatch_action(
        {"action": "run_shell_command", "reason": "Need shell.", "target": "echo ok"},
        tmp_path / "actions.jsonl",
        task_id="task_1",
        confirm=True,
    )

    assert record["permission_level"] == "dangerous"
