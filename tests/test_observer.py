from pathlib import Path

from citta_console.observer import observe


def test_observe_builds_report(tmp_path: Path) -> None:
    trace = tmp_path / "trace.jsonl"
    actions = tmp_path / "actions.jsonl"
    trace.write_text(
        '{"time":"2026-06-07T15:00:00+07:00","task_id":"task_1","agent":"code_agent","framework":"generic","action":"edit_file","target":"src/ui.js","status":"completed"}\n',
        encoding="utf-8",
    )

    report = observe(trace, actions_path=actions)

    assert report["task_id"] == "task_1"
    assert report["current_state"] == "code_changed_no_test"
    assert report["recommended_actions"][0]["action"] == "run_tests"
