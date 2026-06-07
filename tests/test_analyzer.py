from citta_console.analyzer import analyze_current_state, detect_task_progress, summarize_recent_activity


def test_analyzer_detects_code_changed_without_test() -> None:
    events = [
        {
            "time": "2026-06-07T15:00:00+07:00",
            "task_id": "task_1",
            "agent": "code_agent",
            "framework": "generic",
            "action": "edit_file",
            "target": "src/ui.js",
            "status": "completed",
        }
    ]

    analysis = analyze_current_state(events)

    assert analysis["current_state"] == "code_changed_no_test"
    assert analysis["active_agents"] == ["code_agent"]
    assert "code_agent edit_file on src/ui.js" in summarize_recent_activity(events)
    assert detect_task_progress(events)["edited_files"] == ["src/ui.js"]


def test_analyzer_detects_failed_test() -> None:
    events = [
        {
            "time": "2026-06-07T15:00:00+07:00",
            "task_id": "task_1",
            "agent": "test_agent",
            "framework": "generic",
            "action": "run_tests",
            "target": "pytest",
            "status": "failed",
        }
    ]

    assert analyze_current_state(events)["current_state"] == "test_failed"
