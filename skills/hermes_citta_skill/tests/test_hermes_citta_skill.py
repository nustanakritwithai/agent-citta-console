from __future__ import annotations

import json
from pathlib import Path

from skills.hermes_citta_skill.citta_skill import HermesCittaSkill
from skills.hermes_citta_skill.trace_writer import (
    append_citta_event,
    record_file_edit,
    record_test_result,
    record_user_input,
)


def _read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def test_append_citta_event_writes_jsonl(tmp_path: Path) -> None:
    trace_path = tmp_path / "trace.jsonl"

    event = append_citta_event(
        trace_path,
        task_id="task_001",
        action="tool_call",
        output="ok",
    )

    assert event["event_id"] == "evt_001"
    assert _read_jsonl(trace_path)[0]["action"] == "tool_call"


def test_event_id_increments(tmp_path: Path) -> None:
    trace_path = tmp_path / "trace.jsonl"

    first = append_citta_event(trace_path, task_id="task_001", action="first")
    second = append_citta_event(trace_path, task_id="task_001", action="second")

    assert first["event_id"] == "evt_001"
    assert second["event_id"] == "evt_002"


def test_record_user_input_writes_user_input_action(tmp_path: Path) -> None:
    trace_path = tmp_path / "trace.jsonl"

    record_user_input(trace_path, "task_001", "Improve UI")

    assert _read_jsonl(trace_path)[0]["action"] == "user_input"


def test_record_file_edit_writes_edit_file_action(tmp_path: Path) -> None:
    trace_path = tmp_path / "trace.jsonl"

    record_file_edit(trace_path, "task_001", "src/ui.js", output="Updated layout")

    event = _read_jsonl(trace_path)[0]
    assert event["action"] == "edit_file"
    assert event["target"] == "src/ui.js"


def test_record_test_result_failed_writes_status_and_error(tmp_path: Path) -> None:
    trace_path = tmp_path / "trace.jsonl"

    record_test_result(
        trace_path,
        "task_001",
        "python -m pytest",
        "failed",
        error="test_dashboard_rendering failed",
    )

    event = _read_jsonl(trace_path)[0]
    assert event["action"] == "run_tests"
    assert event["status"] == "failed"
    assert event["error"] == "test_dashboard_rendering failed"


def test_hermes_citta_skill_observe_generates_dashboard(tmp_path: Path) -> None:
    trace_path = tmp_path / "citta_trace.jsonl"
    actions_path = tmp_path / "actions.jsonl"
    dashboard_path = tmp_path / "dashboard.html"
    skill = HermesCittaSkill(trace_path, actions_path, dashboard_path)

    skill.record_user_input("task_001", "Improve UI and run tests")
    skill.record_file_edit("task_001", "src/ui.js", output="Updated UI")
    skill.record_test_result(
        "task_001",
        "python -m pytest",
        "failed",
        error="test_dashboard_rendering failed",
    )
    skill.record_file_edit("task_001", "src/renderer.py", output="Changed renderer")
    report = skill.observe(goal="Test Hermes Citta Skill", task_id="task_001")

    risk_types = {risk["type"] for risk in report["risks"]}
    action_names = {action["action"] for action in report["recommended_actions"]}

    assert dashboard_path.exists()
    assert "edit_after_failed_test" in risk_types
    assert "inspect_error" in action_names
    assert "pause" in action_names


def test_skill_does_not_implement_destructive_execution(tmp_path: Path) -> None:
    skill = HermesCittaSkill(
        tmp_path / "trace.jsonl",
        tmp_path / "actions.jsonl",
        tmp_path / "dashboard.html",
    )

    assert not hasattr(skill, "execute_shell")
    assert not hasattr(skill, "deploy")
    assert not hasattr(skill, "git_push")
    assert not hasattr(skill, "delete")
