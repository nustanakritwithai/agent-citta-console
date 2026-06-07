from citta_console.risk_detector import detect_risks


def _event(action: str, status: str, agent: str = "agent", target: str = "target") -> dict[str, str]:
    return {
        "time": "2026-06-07T15:00:00+07:00",
        "task_id": "task_1",
        "agent": agent,
        "framework": "generic",
        "action": action,
        "target": target,
        "status": status,
    }


def test_detects_failed_event_and_edit_after_failed_test() -> None:
    risks = detect_risks(
        [
            _event("run_tests", "failed", agent="test_agent", target="pytest"),
            _event("edit_file", "completed", agent="code_agent", target="src/ui.js"),
        ]
    )
    risk_types = {risk["type"] for risk in risks}

    assert "failed_event_detected" in risk_types
    assert "edit_after_failed_test" in risk_types
    assert "no_test_after_code_edit" in risk_types


def test_detects_repeated_failure_and_loop() -> None:
    events = [_event("run_tests", "failed", agent="test_agent", target="pytest") for _ in range(4)]

    risk_types = {risk["type"] for risk in detect_risks(events)}

    assert "repeated_failure" in risk_types
    assert "loop_detected" in risk_types


def test_detects_dangerous_requested_action() -> None:
    risks = detect_risks([], requested_action={"action": "run_shell_command", "target": "rm -rf"})

    assert risks[0]["type"] == "dangerous_action_requested"
