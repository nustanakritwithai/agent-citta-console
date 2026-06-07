from pathlib import Path

from citta_console.renderer import (
    render_confirmation_page,
    render_dashboard,
    render_dashboard_html,
)


def _report() -> dict[str, object]:
    return {
        "time": "2026-06-07T15:06:00+07:00",
        "task_id": "task_1",
        "current_state": "test_failed_after_file_edit",
        "active_agents": ["code_agent", "test_agent"],
        "recent_events": 1,
        "risks": [
            {
                "type": "edit_after_failed_test",
                "severity": "high",
                "reason": "Edit followed failed test.",
            }
        ],
        "recommended_actions": [
            {
                "action": "inspect_error",
                "label": "Inspect Error",
                "permission_level": "safe",
                "reason": "A failed test needs diagnosis.",
            }
        ],
        "decision": "inspect_error",
        "reason": "A failed test needs diagnosis.",
        "summary": "Code agent edited after test failure.",
        "events": [
            {
                "time": "2026-06-07T15:00:00+07:00",
                "agent": "code_agent",
                "action": "edit_file",
                "target": "src/ui.js",
                "status": "completed",
            }
        ],
        "action_history": [
            {
                "time": "2026-06-07T15:05:00+07:00",
                "action_id": "act_1",
                "task_id": "task_1",
                "action": "run_tests",
                "target": "pytest",
                "permission_level": "medium",
                "status": "pending_confirmation",
                "reason": "Code changed.",
            }
        ],
    }


def test_render_dashboard_html_contains_core_sections() -> None:
    html = render_dashboard_html(_report(), refresh_interval_seconds=5)

    assert "Current State" in html
    assert "Risks" in html
    assert "Recommended Actions" in html
    assert "Inspect Error" in html
    assert "src/ui.js" in html
    assert '<meta http-equiv="refresh" content="5">' in html
    assert "Auto-refresh: every 5 seconds" in html
    assert "Action History" in html
    assert "pending_confirmation" in html
    assert "Confirmation status" in html


def test_render_dashboard_html_shows_refresh_disabled() -> None:
    html = render_dashboard_html(_report(), refresh_interval_seconds=0)

    assert "Auto-refresh: disabled" in html
    assert "http-equiv=\"refresh\"" not in html


def test_render_dashboard_writes_file(tmp_path: Path) -> None:
    output = render_dashboard(_report(), tmp_path / "dashboard.html", refresh_interval_seconds=5)

    assert output.exists()
    assert "Citta Console" in output.read_text(encoding="utf-8")


def test_render_confirmation_page_contains_confirm_and_cancel() -> None:
    html = render_confirmation_page(
        {
            "action_id": "act_1",
            "action": "run_tests",
            "permission_level": "medium",
            "status": "pending_confirmation",
            "reason": "Need tests.",
        }
    )

    assert "Citta Action Confirmation" in html
    assert 'action="/confirm"' in html
    assert 'action="/cancel"' in html
