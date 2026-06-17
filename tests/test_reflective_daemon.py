from __future__ import annotations

import json
from pathlib import Path

from citta_console.cli import main as cli_main
from citta_console.reflective_daemon import (
    ReflectiveDaemonState,
    run_reflective_daemon,
    trace_has_changed,
)
from citta_console.tools import dispatch_tool

FAILED_TEST_TRACE = """\
{"time":"2026-06-07T10:00:00+07:00","event_id":"evt_001","task_id":"task_1","agent":"code_agent","framework":"generic","action":"edit_file","target":"src/ui.js","status":"completed"}
{"time":"2026-06-07T10:01:00+07:00","event_id":"evt_002","task_id":"task_1","agent":"test_agent","framework":"generic","action":"run_tests","target":"python -m pytest","status":"failed","error":"test failed"}
{"time":"2026-06-07T10:02:00+07:00","event_id":"evt_003","task_id":"task_1","agent":"code_agent","framework":"generic","action":"edit_file","target":"src/renderer.py","status":"completed"}
"""

NEW_EVENT = """\
{"time":"2026-06-07T10:03:00+07:00","event_id":"evt_004","task_id":"task_1","agent":"code_agent","framework":"generic","action":"run_tests","target":"python -m pytest","status":"completed"}
"""


def test_daemon_processes_initial_trace(tmp_path: Path) -> None:
    trace = tmp_path / "trace.jsonl"
    reflections = tmp_path / "reflections.jsonl"
    trace.write_text(FAILED_TEST_TRACE, encoding="utf-8")

    result = run_reflective_daemon(
        trace,
        task_id="task_1",
        reflections_path=reflections,
        poll_interval_seconds=0,
        max_cycles=1,
        sleep_fn=lambda _seconds: None,
    )

    assert result["ticks_run"] == 1
    assert result["history"][0]["tick_action"] == "acted"
    assert result["history"][0]["body_action"] == "inspect_error"


def test_daemon_idles_without_trace_change(tmp_path: Path) -> None:
    trace = tmp_path / "trace.jsonl"
    reflections = tmp_path / "reflections.jsonl"
    trace.write_text(FAILED_TEST_TRACE, encoding="utf-8")

    first = run_reflective_daemon(
        trace,
        task_id="task_1",
        reflections_path=reflections,
        poll_interval_seconds=0,
        max_cycles=1,
        sleep_fn=lambda _seconds: None,
    )
    second = run_reflective_daemon(
        trace,
        task_id="task_1",
        reflections_path=reflections,
        poll_interval_seconds=0,
        max_cycles=2,
        sleep_fn=lambda _seconds: None,
    )

    assert first["ticks_run"] == 1
    assert second["ticks_run"] == 1
    assert second["idle_polls"] == 1


def test_daemon_reacts_to_new_trace_event(tmp_path: Path) -> None:
    trace = tmp_path / "trace.jsonl"
    reflections = tmp_path / "reflections.jsonl"
    trace.write_text(FAILED_TEST_TRACE, encoding="utf-8")

    run_reflective_daemon(
        trace,
        task_id="task_1",
        reflections_path=reflections,
        poll_interval_seconds=0,
        max_cycles=1,
        sleep_fn=lambda _seconds: None,
    )

    with trace.open("a", encoding="utf-8") as handle:
        handle.write(NEW_EVENT)

    result = run_reflective_daemon(
        trace,
        task_id="task_1",
        reflections_path=reflections,
        poll_interval_seconds=0,
        max_cycles=1,
        sleep_fn=lambda _seconds: None,
    )

    assert result["ticks_run"] == 1


def test_trace_has_changed_detects_new_events(tmp_path: Path) -> None:
    trace = tmp_path / "trace.jsonl"
    trace.write_text(FAILED_TEST_TRACE, encoding="utf-8")
    state = ReflectiveDaemonState()

    assert trace_has_changed(trace, "task_1", state) is True
    state.last_trace_mtime = trace.stat().st_mtime
    state.last_trace_size = trace.stat().st_size
    state.last_event_count = 3

    assert trace_has_changed(trace, "task_1", state) is False

    with trace.open("a", encoding="utf-8") as handle:
        handle.write(NEW_EVENT)

    assert trace_has_changed(trace, "task_1", state) is True


def test_cli_loop_daemon_with_max_cycles(capsys, tmp_path: Path) -> None:
    trace = tmp_path / "trace.jsonl"
    reflections = tmp_path / "reflections.jsonl"
    trace.write_text(FAILED_TEST_TRACE, encoding="utf-8")

    exit_code = cli_main(
        [
            "loop",
            "daemon",
            "--trace",
            str(trace),
            "--reflections",
            str(reflections),
            "--task-id",
            "task_1",
            "--poll-interval",
            "0",
            "--max-cycles",
            "1",
        ]
    )

    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == 0
    assert payload["ok"] is True
    assert payload["ticks_run"] == 1
    assert payload["stop_reason"] == "max_cycles"


def test_run_reflective_daemon_tool_works(tmp_path: Path) -> None:
    trace = tmp_path / "trace.jsonl"
    reflections = tmp_path / "reflections.jsonl"
    trace.write_text(FAILED_TEST_TRACE, encoding="utf-8")

    result = dispatch_tool(
        "citta.run_reflective_daemon",
        {
            "trace_path": str(trace),
            "task_id": "task_1",
            "reflections_path": str(reflections),
            "poll_interval_seconds": 0,
            "max_cycles": 1,
        },
    )

    assert result["ok"] is True
    assert result["ticks_run"] == 1
