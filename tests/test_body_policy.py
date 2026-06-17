from __future__ import annotations

import json
from pathlib import Path

from citta_console.body_policy import (
    append_reflective_trace_event,
    choose_action_from_reflection,
    extract_body_loop_status,
    is_lesson_applied,
    parse_recommended_action,
    plan_reflective_action,
)
from citta_console.observer import observe
from citta_console.storage import read_jsonl


REFLECTION = {
    "time": "2026-06-07T10:05:00+07:00",
    "reflection_id": "ref_loop001",
    "task_id": "task_1",
    "goal": "Keep tests passing",
    "action": "code_agent edit_file on src/renderer.py (completed)",
    "result": "test_failed_after_file_edit",
    "risk_or_mistake": "edit_after_failed_test: edits continued after failure.",
    "lesson": "Inspect failing test output before making more file edits.",
    "next_recommendation": "inspect_error: A test failed and edits continued afterward.",
    "agent": "citta_observer",
}


FAILED_TEST_TRACE = """\
{"time":"2026-06-07T10:00:00+07:00","event_id":"evt_001","task_id":"task_1","agent":"code_agent","framework":"generic","action":"edit_file","target":"src/ui.js","status":"completed"}
{"time":"2026-06-07T10:01:00+07:00","event_id":"evt_002","task_id":"task_1","agent":"test_agent","framework":"generic","action":"run_tests","target":"python -m pytest","status":"failed","error":"test failed"}
{"time":"2026-06-07T10:02:00+07:00","event_id":"evt_003","task_id":"task_1","agent":"code_agent","framework":"generic","action":"edit_file","target":"src/renderer.py","status":"completed"}
"""


def test_parse_recommended_action_reads_action_name() -> None:
    assert parse_recommended_action(REFLECTION) == "inspect_error"


def test_choose_action_from_reflection_matches_recommendation() -> None:
    action, reason = choose_action_from_reflection(REFLECTION)

    assert action == "inspect_error"
    assert "inspect_error" in reason
    assert is_lesson_applied(REFLECTION, action) is True


def test_choose_action_falls_back_without_reflection() -> None:
    action, reason = choose_action_from_reflection(None, fallback="edit_file")

    assert action == "edit_file"
    assert is_lesson_applied(REFLECTION, action) is False
    assert "No reflection available" in reason


def test_append_reflective_trace_event_records_lesson_application(tmp_path: Path) -> None:
    trace = tmp_path / "trace.jsonl"
    reflections = tmp_path / "reflections.jsonl"
    trace.write_text(FAILED_TEST_TRACE, encoding="utf-8")
    with reflections.open("w", encoding="utf-8") as handle:
        handle.write(json.dumps(REFLECTION, sort_keys=True) + "\n")

    event = append_reflective_trace_event(
        trace,
        reflections,
        task_id="task_1",
    )

    stored = read_jsonl(trace)[-1]
    assert stored["action"] == "inspect_error"
    assert stored["metadata"]["lesson_applied"] is True
    assert stored["metadata"]["source_reflection_id"] == "ref_loop001"
    assert stored["metadata"]["inspected_error"] is True
    assert event["event_id"] == stored["event_id"]


def test_extract_body_loop_status_reads_latest_reflective_event() -> None:
    events = [
        {
            "agent": "reflective_body_agent",
            "metadata": {
                "reflective_body_agent": True,
                "lesson_applied": True,
                "applied_recommendation": "inspect_error",
                "source_reflection_id": "ref_loop001",
            },
        }
    ]

    status = extract_body_loop_status(events)

    assert status["lesson_applied"] is True
    assert status["body_loop_status"] == "lesson_applied"
    assert status["applied_recommendation"] == "inspect_error"


def test_observe_reports_body_loop_status_after_reflective_body_act(
    tmp_path: Path,
) -> None:
    trace = tmp_path / "trace.jsonl"
    reflections = tmp_path / "reflections.jsonl"
    trace.write_text(FAILED_TEST_TRACE, encoding="utf-8")

    observe(
        trace,
        task_id="task_1",
        goal="Keep tests passing",
        reflections_path=reflections,
        record_reflection=True,
    )
    append_reflective_trace_event(trace, reflections, task_id="task_1")

    report = observe(
        trace,
        task_id="task_1",
        goal="Keep tests passing",
        reflections_path=reflections,
    )

    assert report["body_loop_status"]["lesson_applied"] is True
    assert report["body_loop_status"]["body_loop_status"] == "lesson_applied"
    assert report["body_loop_status"]["applied_recommendation"] == "inspect_error"


def test_plan_reflective_action_without_writing_trace(tmp_path: Path) -> None:
    reflections = tmp_path / "reflections.jsonl"
    with reflections.open("w", encoding="utf-8") as handle:
        handle.write(json.dumps(REFLECTION, sort_keys=True) + "\n")

    plan = plan_reflective_action(str(reflections), task_id="task_1")

    assert plan["action"] == "inspect_error"
    assert plan["lesson_applied"] is True
