from __future__ import annotations

import json
from pathlib import Path

from citta_console.cli import main as cli_main
from citta_console.reflective_loop import run_reflective_loop
from citta_console.tools import dispatch_tool


FAILED_TEST_TRACE = """\
{"time":"2026-06-07T10:00:00+07:00","event_id":"evt_001","task_id":"task_1","agent":"code_agent","framework":"generic","action":"edit_file","target":"src/ui.js","status":"completed"}
{"time":"2026-06-07T10:01:00+07:00","event_id":"evt_002","task_id":"task_1","agent":"test_agent","framework":"generic","action":"run_tests","target":"python -m pytest","status":"failed","error":"test failed"}
{"time":"2026-06-07T10:02:00+07:00","event_id":"evt_003","task_id":"task_1","agent":"code_agent","framework":"generic","action":"edit_file","target":"src/renderer.py","status":"completed"}
"""


def test_run_reflective_loop_applies_lesson_and_stops(tmp_path: Path) -> None:
    trace = tmp_path / "trace.jsonl"
    reflections = tmp_path / "reflections.jsonl"
    trace.write_text(FAILED_TEST_TRACE, encoding="utf-8")
    reflections.write_text("", encoding="utf-8")

    result = run_reflective_loop(
        trace,
        task_id="task_1",
        goal="Keep tests passing",
        reflections_path=reflections,
        max_iterations=3,
    )

    assert result["ok"] is True
    assert result["stop_reason"] == "lesson_applied"
    assert result["iterations"] == 1
    assert result["steps"][0]["body_action"] == "inspect_error"
    assert result["steps"][0]["lesson_applied"] is True
    assert result["final_report"]["body_loop_status"]["lesson_applied"] is True


def test_run_reflective_loop_stops_when_body_blocks(tmp_path: Path) -> None:
    trace = tmp_path / "trace.jsonl"
    reflections = tmp_path / "reflections.jsonl"
    trace.write_text(FAILED_TEST_TRACE, encoding="utf-8")
    reflections.write_text("", encoding="utf-8")

    for index in range(3):
        record = {
            "time": f"2026-06-07T10:0{index}:00+07:00",
            "reflection_id": f"ref_{index}",
            "task_id": "task_1",
            "goal": "Keep tests passing",
            "action": "code_agent edit_file",
            "result": "test_failed_after_file_edit",
            "risk_or_mistake": "edit_after_failed_test: edits continued.",
            "lesson": "Inspect failing test output before making more file edits.",
            "next_recommendation": "ask_user: The same lesson was recorded multiple times.",
            "agent": "citta_observer",
        }
        with reflections.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, sort_keys=True) + "\n")

    result = run_reflective_loop(
        trace,
        task_id="task_1",
        reflections_path=reflections,
        max_iterations=3,
    )

    assert result["stop_reason"] == "body_blocked"
    assert result["steps"][-1]["body_action"] == "ask_user"


def test_run_reflective_loop_tool_works(tmp_path: Path) -> None:
    trace = tmp_path / "trace.jsonl"
    reflections = tmp_path / "reflections.jsonl"
    trace.write_text(FAILED_TEST_TRACE, encoding="utf-8")

    result = dispatch_tool(
        "citta.run_reflective_loop",
        {
            "trace_path": str(trace),
            "task_id": "task_1",
            "reflections_path": str(reflections),
            "max_iterations": 2,
        },
    )

    assert result["ok"] is True
    assert result["stop_reason"] == "lesson_applied"


def test_cli_loop_run_emits_json(capsys, tmp_path: Path) -> None:
    trace = tmp_path / "trace.jsonl"
    reflections = tmp_path / "reflections.jsonl"
    trace.write_text(FAILED_TEST_TRACE, encoding="utf-8")

    exit_code = cli_main(
        [
            "loop",
            "run",
            "--trace",
            str(trace),
            "--reflections",
            str(reflections),
            "--task-id",
            "task_1",
            "--max-iterations",
            "2",
        ]
    )

    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == 0
    assert payload["ok"] is True
    assert payload["stop_reason"] == "lesson_applied"
