from pathlib import Path

from citta_console.config import CittaConfig
from citta_console.server import (
    build_report,
    handle_action_submission,
    handle_cancel_submission,
    handle_confirm_submission,
    parse_form_body,
)


def _config(tmp_path: Path) -> CittaConfig:
    trace_path = tmp_path / "trace.jsonl"
    actions_path = tmp_path / "actions.jsonl"
    trace_path.write_text(
        '{"time":"2026-06-07T15:00:00+07:00","task_id":"task_1","agent":"code_agent","framework":"generic","action":"edit_file","target":"src/ui.js","status":"completed"}\n',
        encoding="utf-8",
    )
    return CittaConfig(
        trace_path=str(trace_path),
        actions_path=str(actions_path),
        dashboard_path=str(tmp_path / "dashboard.html"),
        refresh_interval_seconds=0,
    )


def test_parse_form_body() -> None:
    assert parse_form_body("action=run_tests&reason=Need+tests") == {
        "action": "run_tests",
        "reason": "Need tests",
    }


def test_build_report_filters_task(tmp_path: Path) -> None:
    report = build_report(_config(tmp_path), task_id="task_1")

    assert report["task_id"] == "task_1"
    assert report["current_state"] == "code_changed_no_test"


def test_handle_action_submission_records_pending_medium_action(tmp_path: Path) -> None:
    record = handle_action_submission(
        {"action": "run_tests", "reason": "Need tests.", "task_id": "task_1"},
        _config(tmp_path),
    )

    assert record["status"] == "pending_confirmation"
    assert record["permission_level"] == "medium"


def test_handle_confirm_and_cancel_submission(tmp_path: Path) -> None:
    config = _config(tmp_path)
    pending = handle_action_submission(
        {"action": "run_tests", "reason": "Need tests.", "task_id": "task_1"},
        config,
    )

    confirmed = handle_confirm_submission({"action_id": pending["action_id"]}, config)
    cancelled = handle_cancel_submission({"action_id": pending["action_id"]}, config)

    assert confirmed["status"] == "confirmed"
    assert cancelled["status"] == "blocked"
