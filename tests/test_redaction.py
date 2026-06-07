from __future__ import annotations

import json
from pathlib import Path

from citta_console.observer import observe
from citta_console.redaction import REDACTED, redact_event, redact_text, redact_value
from citta_console.skills.hermes_citta_skill.runtime_hook import HermesRuntimeTraceHook
from citta_console.skills.hermes_citta_skill.trace_writer import append_citta_event


def _read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def test_redact_bearer_token() -> None:
    assert redact_text("Authorization: Bearer abc123") == "Authorization: Bearer [REDACTED]"


def test_redact_authorization_header() -> None:
    assert redact_text("Authorization: Basic abc123") == "Authorization: [REDACTED]"


def test_redact_openai_api_key_env_style() -> None:
    assert redact_text("OPENAI_API_KEY=sk-abc123456789") == "OPENAI_API_KEY=[REDACTED]"


def test_redact_dict_key_password() -> None:
    assert redact_value({"password": "abc"}) == {"password": REDACTED}


def test_redact_dict_key_token() -> None:
    assert redact_value({"token": "abc"}) == {"token": REDACTED}


def test_redact_cookie_key() -> None:
    assert redact_value({"cookie": "sessionid=abc"}) == {"cookie": REDACTED}


def test_redact_nested_secret() -> None:
    payload = {"metadata": {"nested": [{"token": "abc"}, {"safe": "ok"}]}}

    assert redact_value(payload) == {"metadata": {"nested": [{"token": REDACTED}, {"safe": "ok"}]}}


def test_redact_private_key_block() -> None:
    text = "before -----BEGIN PRIVATE KEY-----\nabc\n-----END PRIVATE KEY----- after"

    assert redact_text(text) == "before [REDACTED] after"


def test_redact_github_token() -> None:
    token = "ghp_abcdefghijklmnopqrstuvwxyz123456"

    assert redact_text(f"token={token}") == "token=[REDACTED]"


def test_non_secret_text_remains_mostly_unchanged() -> None:
    text = "Improve UI and keep tests passing"

    assert redact_text(text) == text


def test_redact_event_preserves_identity_fields() -> None:
    event = {
        "time": "2026-06-07T00:00:00+00:00",
        "event_id": "evt_001",
        "task_id": "task_001",
        "agent": "hermes",
        "framework": "hermes",
        "action": "edit_file",
        "status": "completed",
        "metadata": {"api_key": "sk-abc123456789"},
    }

    redacted = redact_event(event)

    assert redacted["event_id"] == "evt_001"
    assert redacted["task_id"] == "task_001"
    assert redacted["action"] == "edit_file"
    assert redacted["metadata"] == {"api_key": REDACTED}


def test_append_citta_event_writes_redacted_output(tmp_path: Path) -> None:
    trace_path = tmp_path / "trace.jsonl"

    append_citta_event(
        trace_path,
        task_id="task_001",
        action="tool_call",
        output="Authorization: Bearer abc123",
        metadata={"OPENAI_API_KEY": "sk-abc123456789"},
    )

    event = _read_jsonl(trace_path)[0]
    assert event["output"] == "Authorization: Bearer [REDACTED]"
    assert event["metadata"]["OPENAI_API_KEY"] == REDACTED
    assert "abc123" not in trace_path.read_text(encoding="utf-8")
    assert "sk-abc" not in trace_path.read_text(encoding="utf-8")


def test_hermes_runtime_trace_hook_writes_redacted_metadata_error_output(tmp_path: Path) -> None:
    trace_path = tmp_path / "trace.jsonl"
    hook = HermesRuntimeTraceHook(trace_path, enabled=True, default_task_id="task_001")

    hook.record_command_result(
        "python -m pytest",
        status="failed",
        output="Cookie: sessionid=abc",
        error="Authorization: Bearer abc123",
        metadata={"token": "ghp_abcdefghijklmnopqrstuvwxyz123456"},
    )

    raw = trace_path.read_text(encoding="utf-8")
    event = _read_jsonl(trace_path)[0]
    assert event["output"] == "Cookie: [REDACTED]"
    assert event["error"] == "Authorization: Bearer [REDACTED]"
    assert event["metadata"]["token"] == REDACTED
    assert "sessionid=abc" not in raw
    assert "abc123" not in raw
    assert "ghp_abcdefghijklmnopqrstuvwxyz" not in raw


def test_recommended_action_logic_still_works_after_redaction(tmp_path: Path) -> None:
    trace_path = tmp_path / "trace.jsonl"
    task_id = "task_001"

    append_citta_event(
        trace_path,
        task_id=task_id,
        action="edit_file",
        target="src/ui.py",
        status="completed",
        metadata={"confidence": 0.62, "goal_alignment": "medium", "api_key": "sk-abc123456789"},
    )
    append_citta_event(
        trace_path,
        task_id=task_id,
        agent="test_agent",
        action="run_tests",
        target="python -m pytest",
        status="failed",
        error="test failed with Authorization: Bearer abc123",
    )
    append_citta_event(
        trace_path,
        task_id=task_id,
        action="edit_file",
        target="src/ui.py",
        status="completed",
        metadata={
            "confidence": 0.4,
            "goal_alignment": "low",
            "inspected_error": False,
            "risk_hint": "goal_drift_possible",
        },
    )

    report = observe(trace_path, goal="Hermes runtime hook demo", task_id=task_id)
    risks = {risk["type"] for risk in report["risks"]}
    actions = {action["action"] for action in report["recommended_actions"]}

    assert {"failed_event_detected", "edit_after_failed_test", "no_test_after_code_edit", "goal_drift_possible"}.issubset(risks)
    assert {"inspect_error", "pause", "run_tests", "view_diff", "redirect"}.issubset(actions)
