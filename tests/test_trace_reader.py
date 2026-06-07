from pathlib import Path

from citta_console.trace_reader import (
    filter_events_by_status,
    filter_events_by_task,
    get_active_agents,
    read_recent_events,
    read_trace,
)


def test_read_trace_skips_bad_lines(tmp_path: Path) -> None:
    trace = tmp_path / "trace.jsonl"
    trace.write_text(
        "\n".join(
            [
                '{"time":"2026-06-07T15:00:00+07:00","task_id":"task_1","agent":"code_agent","framework":"generic","action":"edit_file","status":"completed"}',
                "not json",
                '{"time":"2026-06-07T15:01:00+07:00","task_id":"task_1","agent":"test_agent","framework":"generic","action":"run_tests","status":"running"}',
            ]
        ),
        encoding="utf-8",
    )

    events = read_trace(trace)

    assert len(events) == 2
    assert events[0].agent == "code_agent"
    assert read_recent_events(trace, limit=1)[0].agent == "test_agent"
    assert filter_events_by_task(events, "task_1") == events
    assert filter_events_by_status(events, "running")[0].agent == "test_agent"
    assert get_active_agents(events) == ["test_agent"]
