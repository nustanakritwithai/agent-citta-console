from __future__ import annotations

import json
from pathlib import Path

import pytest

from citta_console.analyzer import analyze_current_state
from citta_console.observer import observe
from citta_console.recommender import recommend_actions
from citta_console.reflection import (
    build_reflection,
    read_reflections,
    record_reflection_from_observation,
    write_reflection,
)
from citta_console.risk_detector import detect_risks
from citta_console.schemas import validate_reflection
from citta_console.storage import read_jsonl


FAILED_TEST_TRACE = """\
{"time":"2026-06-07T10:00:00+07:00","event_id":"evt_001","task_id":"task_1","agent":"code_agent","framework":"generic","action":"edit_file","target":"src/ui.js","status":"completed"}
{"time":"2026-06-07T10:01:00+07:00","event_id":"evt_002","task_id":"task_1","agent":"test_agent","framework":"generic","action":"run_tests","target":"python -m pytest","status":"failed","error":"test failed"}
{"time":"2026-06-07T10:02:00+07:00","event_id":"evt_003","task_id":"task_1","agent":"code_agent","framework":"generic","action":"edit_file","target":"src/renderer.py","status":"completed"}
"""


def _load_events(trace_text: str) -> list[dict]:
    return [json.loads(line) for line in trace_text.strip().splitlines() if line.strip()]


def test_build_reflection_captures_goal_action_result_and_lesson() -> None:
    events = _load_events(FAILED_TEST_TRACE)
    analysis = analyze_current_state(events, goal="Keep tests passing")
    risks = detect_risks(events, goal="Keep tests passing")
    recommendations = recommend_actions(analysis, risks)

    reflection = build_reflection(
        events,
        analysis,
        risks,
        recommendations,
        task_id="task_1",
        goal="Keep tests passing",
    )

    assert reflection["goal"] == "Keep tests passing"
    assert "edit_file" in reflection["action"]
    assert reflection["result"].startswith("test_failed_after_file_edit")
    assert "edit_after_failed_test" in reflection["risk_or_mistake"]
    assert "Inspect failing test output" in reflection["lesson"]
    assert reflection["next_recommendation"].startswith("inspect_error:")
    assert reflection["metadata"]["recommended_action"] == "inspect_error"


def test_write_and_read_reflections_round_trip(tmp_path: Path) -> None:
    reflections_path = tmp_path / "reflections.jsonl"
    record = {
        "time": "2026-06-07T10:05:00+07:00",
        "reflection_id": "ref_test001",
        "task_id": "task_1",
        "goal": "Ship safely",
        "action": "code_agent edit_file on src/ui.js (completed)",
        "result": "code_changed_no_test: recent activity summary.",
        "risk_or_mistake": "no_test_after_code_edit: Code changed without a later test event.",
        "lesson": "Run tests after code changes to catch regressions early.",
        "next_recommendation": "run_tests: Code changed without a later test event.",
    }

    written = write_reflection(reflections_path, record)
    loaded = read_reflections(reflections_path, task_id="task_1")

    assert written["reflection_id"] == "ref_test001"
    assert len(loaded) == 1
    assert loaded[0]["lesson"] == record["lesson"]


def test_validate_reflection_requires_core_fields() -> None:
    with pytest.raises(ValueError, match="reflection missing required fields"):
        validate_reflection({"task_id": "task_1", "goal": "only partial data"})


def test_observe_records_reflection_when_enabled(tmp_path: Path) -> None:
    trace = tmp_path / "trace.jsonl"
    reflections = tmp_path / "reflections.jsonl"
    trace.write_text(FAILED_TEST_TRACE, encoding="utf-8")

    report = observe(
        trace,
        task_id="task_1",
        goal="Keep tests passing",
        reflections_path=reflections,
        record_reflection=True,
    )

    stored = read_jsonl(reflections)

    assert report["reflection"]["task_id"] == "task_1"
    assert report["reflection_history"]
    assert len(stored) == 1
    assert stored[0]["reflection_id"] == report["reflection"]["reflection_id"]
    assert "Inspect failing test output" in stored[0]["lesson"]


def test_record_reflection_from_observation_appends_jsonl(tmp_path: Path) -> None:
    events = _load_events(FAILED_TEST_TRACE)
    analysis = analyze_current_state(events)
    risks = detect_risks(events)
    recommendations = recommend_actions(analysis, risks)
    reflections_path = tmp_path / "reflections.jsonl"

    record_reflection_from_observation(
        events,
        analysis,
        risks,
        recommendations,
        reflections_path,
        task_id="task_1",
        goal="Keep tests passing",
    )

    records = read_reflections(reflections_path)
    assert len(records) == 1
    assert records[0]["goal"] == "Keep tests passing"
    assert records[0]["next_recommendation"].startswith("inspect_error:")
