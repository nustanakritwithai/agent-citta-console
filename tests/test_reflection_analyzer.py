from __future__ import annotations

import json
from pathlib import Path

from citta_console.analyzer import analyze_current_state
from citta_console.observer import observe
from citta_console.recommender import recommend_actions
from citta_console.reflection_analyzer import (
    analyze_reflection_history,
    detect_reflection_risks,
)
from citta_console.risk_detector import detect_risks


LESSON_TEXT = "Inspect failing test output before making more file edits."
MISTAKE_TEXT = (
    "failed_event_detected: test failed.; "
    "edit_after_failed_test: edits continued after failure."
)


def _reflection(lesson: str = LESSON_TEXT, mistake: str = MISTAKE_TEXT) -> dict[str, str]:
    return {
        "time": "2026-06-07T10:05:00+07:00",
        "reflection_id": "ref_sample",
        "task_id": "task_1",
        "goal": "Keep tests passing",
        "action": "code_agent edit_file on src/renderer.py (completed)",
        "result": "test_failed_after_file_edit",
        "risk_or_mistake": mistake,
        "lesson": lesson,
        "next_recommendation": "inspect_error: A test failed and edits continued afterward.",
        "agent": "citta_observer",
        "metadata": {"current_state": "test_failed_after_file_edit"},
    }


FAILED_TEST_TRACE = """\
{"time":"2026-06-07T10:00:00+07:00","event_id":"evt_001","task_id":"task_1","agent":"code_agent","framework":"generic","action":"edit_file","target":"src/ui.js","status":"completed"}
{"time":"2026-06-07T10:01:00+07:00","event_id":"evt_002","task_id":"task_1","agent":"test_agent","framework":"generic","action":"run_tests","target":"python -m pytest","status":"failed","error":"test failed"}
{"time":"2026-06-07T10:02:00+07:00","event_id":"evt_003","task_id":"task_1","agent":"code_agent","framework":"generic","action":"edit_file","target":"src/renderer.py","status":"completed"}
"""


def _load_events(trace_text: str) -> list[dict]:
    return [json.loads(line) for line in trace_text.strip().splitlines() if line.strip()]


def test_analyze_reflection_history_detects_repeated_lesson() -> None:
    reflections = [_reflection() for _ in range(3)]
    events = _load_events(FAILED_TEST_TRACE)
    analysis = analyze_current_state(events)

    insights = analyze_reflection_history(reflections, events=events, analysis=analysis)

    assert insights["total_reflections"] == 3
    assert insights["most_repeated_lesson_count"] == 3
    assert insights["repeated_lesson_ignored"] is True
    assert len(insights["repeated_lessons"]) == 1


def test_detect_reflection_risks_flags_same_mistake_twice() -> None:
    reflections = [_reflection() for _ in range(2)]
    insights = analyze_reflection_history(reflections)

    risks = detect_reflection_risks(insights)
    risk_types = {risk["type"] for risk in risks}

    assert "same_mistake_twice" in risk_types


def test_detect_reflection_risks_flags_repeated_lesson_ignored() -> None:
    reflections = [_reflection() for _ in range(3)]
    events = _load_events(FAILED_TEST_TRACE)
    analysis = analyze_current_state(events)
    insights = analyze_reflection_history(reflections, events=events, analysis=analysis)

    risks = detect_reflection_risks(insights, events=events, analysis=analysis)
    risk_types = {risk["type"] for risk in risks}

    assert "repeated_lesson_ignored" in risk_types


def test_recommender_prioritizes_ask_user_when_lesson_ignored() -> None:
    events = _load_events(FAILED_TEST_TRACE)
    analysis = analyze_current_state(events)
    trace_risks = detect_risks(events)
    insights = analyze_reflection_history(
        [_reflection() for _ in range(3)],
        events=events,
        analysis=analysis,
    )
    reflection_risks = detect_reflection_risks(insights, events=events, analysis=analysis)
    risks = trace_risks + reflection_risks

    actions = recommend_actions(analysis, risks, insights)

    assert actions[0]["action"] == "ask_user"
    assert actions[1]["action"] == "pause"
    assert all(action["action"] != "inspect_error" for action in actions)


def test_observe_includes_reflection_insights_and_lesson_aware_decision(
    tmp_path: Path,
) -> None:
    trace = tmp_path / "trace.jsonl"
    reflections = tmp_path / "reflections.jsonl"
    trace.write_text(FAILED_TEST_TRACE, encoding="utf-8")

    for index in range(3):
        record = _reflection()
        record["reflection_id"] = f"ref_{index}"
        with reflections.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")

    report = observe(
        trace,
        task_id="task_1",
        goal="Keep tests passing",
        reflections_path=reflections,
    )

    assert report["reflection_insights"]["repeated_lesson_ignored"] is True
    assert report["decision"] == "ask_user"
    risk_types = {risk["type"] for risk in report["risks"]}
    assert "repeated_lesson_ignored" in risk_types
