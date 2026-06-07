from __future__ import annotations

import json
from pathlib import Path

from citta_console.skills.hermes_citta_skill import HermesCittaSkill
from citta_console.skills.hermes_citta_skill.trace_writer import (
    record_file_edit,
    record_final_answer,
    record_test_result,
    record_tool_call,
    record_user_input,
)


def _read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def test_record_file_edit_preserves_metadata_fields(tmp_path: Path) -> None:
    trace_path = tmp_path / "trace.jsonl"

    record_file_edit(
        trace_path,
        "task_001",
        "src/ui.js",
        output="Updated layout",
        metadata={
            "confidence": 0.45,
            "goal_alignment": "low",
            "reason": "continued visual refactor despite failing test",
            "inspected_error": False,
            "source_state": "test_failed_after_file_edit",
            "risk_hint": "goal_drift_possible",
            "notes": "metadata-backed signal quality trial",
        },
    )

    metadata = _read_jsonl(trace_path)[0]["metadata"]
    assert metadata["source"] == "hermes_citta_skill"
    assert metadata["files_changed"] == ["src/ui.js"]
    assert metadata["confidence"] == 0.45
    assert metadata["goal_alignment"] == "low"
    assert metadata["reason"] == "continued visual refactor despite failing test"
    assert metadata["inspected_error"] is False
    assert metadata["source_state"] == "test_failed_after_file_edit"
    assert metadata["risk_hint"] == "goal_drift_possible"
    assert metadata["notes"] == "metadata-backed signal quality trial"


def test_all_hermes_trace_helpers_accept_metadata(tmp_path: Path) -> None:
    trace_path = tmp_path / "trace.jsonl"
    metadata = {"confidence": 0.9, "source_state": "unit_test"}

    record_user_input(trace_path, "task_001", "Improve UI", metadata=metadata)
    record_tool_call(trace_path, "task_001", "read_file", metadata=metadata)
    record_file_edit(trace_path, "task_001", "src/ui.js", metadata=metadata)
    record_test_result(trace_path, "task_001", "python -m pytest", "completed", metadata=metadata)
    record_final_answer(trace_path, "task_001", "Done", metadata=metadata)

    events = _read_jsonl(trace_path)
    assert len(events) == 5
    assert all(event["metadata"]["confidence"] == 0.9 for event in events)
    assert all(event["metadata"]["source_state"] == "unit_test" for event in events)


def test_metadata_backed_goal_drift_triggers_redirect(tmp_path: Path) -> None:
    trace_path = tmp_path / "citta_trace.jsonl"
    actions_path = tmp_path / "actions.jsonl"
    dashboard_path = tmp_path / "dashboard.html"
    skill = HermesCittaSkill(trace_path, actions_path, dashboard_path)

    task_id = "hermes_metadata_goal_drift_001"
    skill.record_user_input(task_id, "Improve UI and fix test failures")
    skill.record_file_edit(
        task_id,
        "src/ui.py",
        output="Started visual refactor",
        metadata={
            "confidence": 0.45,
            "goal_alignment": "low",
            "reason": "continued visual refactor despite failing test",
            "inspected_error": False,
            "source_state": "pre_test_edit",
        },
    )
    skill.record_test_result(
        task_id,
        "python -m pytest",
        "failed",
        error="test_dashboard_rendering failed",
        metadata={"source_state": "test_failed", "inspected_error": False},
    )
    skill.record_file_edit(
        task_id,
        "src/theme.py",
        output="Continued styling changes",
        metadata={
            "confidence": 0.4,
            "goal_alignment": "low",
            "reason": "continued visual refactor despite failing test",
            "inspected_error": False,
            "source_state": "test_failed_after_file_edit",
            "risk_hint": "goal_drift_possible",
        },
    )

    report = skill.observe(goal="Improve UI and fix test failures", task_id=task_id)
    risk_types = {risk["type"] for risk in report["risks"]}
    action_names = {action["action"] for action in report["recommended_actions"]}

    assert "failed_event_detected" in risk_types
    assert "edit_after_failed_test" in risk_types
    assert "no_test_after_code_edit" in risk_types
    assert "goal_drift_possible" in risk_types
    assert {"inspect_error", "pause", "run_tests", "view_diff", "redirect"}.issubset(action_names)
    assert dashboard_path.exists()
