from __future__ import annotations

import json
from pathlib import Path

from citta_console.skills.hermes_citta_skill import HermesRuntimeTraceHook, hook_config_from_env
from citta_console.skills.hermes_citta_skill.citta_skill import HermesCittaSkill


def _read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def test_disabled_hook_does_not_write_trace(tmp_path: Path) -> None:
    trace_path = tmp_path / "trace.jsonl"
    hook = HermesRuntimeTraceHook(trace_path, enabled=False, default_task_id="task_001")

    result = hook.record_user_input("Improve UI")

    assert result is None
    assert not trace_path.exists()


def test_enabled_hook_writes_trace(tmp_path: Path) -> None:
    trace_path = tmp_path / "trace.jsonl"
    hook = HermesRuntimeTraceHook(trace_path, enabled=True, default_task_id="task_001")

    event = hook.record_user_input("Improve UI")

    assert event is not None
    assert trace_path.exists()
    assert _read_jsonl(trace_path)[0]["task_id"] == "task_001"


def test_user_input_maps_correctly(tmp_path: Path) -> None:
    hook = HermesRuntimeTraceHook(tmp_path / "trace.jsonl", enabled=True, default_task_id="task_001")

    hook.record_user_input("Improve UI")

    event = _read_jsonl(hook.trace_path)[0]
    assert event["agent"] == "user"
    assert event["action"] == "user_input"
    assert event["input"] == "Improve UI"


def test_tool_call_maps_to_tool_name(tmp_path: Path) -> None:
    hook = HermesRuntimeTraceHook(tmp_path / "trace.jsonl", enabled=True, default_task_id="task_001")

    hook.record_tool_call("read_file", target="src/ui.py", output="ok")

    event = _read_jsonl(hook.trace_path)[0]
    assert event["action"] == "read_file"
    assert event["metadata"]["tool"] == "read_file"


def test_file_edit_maps_to_edit_file(tmp_path: Path) -> None:
    hook = HermesRuntimeTraceHook(tmp_path / "trace.jsonl", enabled=True, default_task_id="task_001")

    hook.record_file_edit("src/ui.py", output="edited")

    event = _read_jsonl(hook.trace_path)[0]
    assert event["action"] == "edit_file"
    assert event["target"] == "src/ui.py"
    assert event["metadata"]["files_changed"] == ["src/ui.py"]


def test_command_result_pytest_maps_to_run_tests(tmp_path: Path) -> None:
    hook = HermesRuntimeTraceHook(tmp_path / "trace.jsonl", enabled=True, default_task_id="task_001")

    hook.record_command_result("python -m pytest", status="failed", error="failed")

    event = _read_jsonl(hook.trace_path)[0]
    assert event["action"] == "run_tests"
    assert event["agent"] == "test_agent"
    assert event["status"] == "failed"


def test_command_result_general_maps_to_command_result(tmp_path: Path) -> None:
    hook = HermesRuntimeTraceHook(tmp_path / "trace.jsonl", enabled=True, default_task_id="task_001")

    hook.record_command_result("python scripts/build_index.py", output="ok")

    event = _read_jsonl(hook.trace_path)[0]
    assert event["action"] == "command_result"
    assert event["target"] == "python scripts/build_index.py"


def test_error_maps_to_failed_event(tmp_path: Path) -> None:
    hook = HermesRuntimeTraceHook(tmp_path / "trace.jsonl", enabled=True, default_task_id="task_001")

    hook.record_error("boom", target="runtime")

    event = _read_jsonl(hook.trace_path)[0]
    assert event["action"] == "error"
    assert event["status"] == "failed"
    assert event["error"] == "boom"


def test_final_answer_maps_correctly(tmp_path: Path) -> None:
    hook = HermesRuntimeTraceHook(tmp_path / "trace.jsonl", enabled=True, default_task_id="task_001")

    hook.record_final_answer("Done")

    event = _read_jsonl(hook.trace_path)[0]
    assert event["action"] == "final_answer"
    assert event["output"] == "Done"


def test_vipaka_check_maps_correctly(tmp_path: Path) -> None:
    hook = HermesRuntimeTraceHook(tmp_path / "trace.jsonl", enabled=True, default_task_id="task_001")

    hook.record_vipaka_check("Reviewed result", target="validation")

    event = _read_jsonl(hook.trace_path)[0]
    assert event["action"] == "vipaka_check"
    assert event["output"] == "Reviewed result"


def test_metadata_merge_preserves_requested_signal_keys(tmp_path: Path) -> None:
    hook = HermesRuntimeTraceHook(
        tmp_path / "trace.jsonl",
        enabled=True,
        default_task_id="task_001",
        default_metadata={
            "confidence": 0.1,
            "goal_alignment": "low",
            "reason": "default",
            "inspected_error": True,
            "source_state": "default_state",
            "risk_hint": "default_hint",
            "notes": "default notes",
        },
    )

    hook.record_file_edit(
        "src/ui.py",
        metadata={
            "confidence": 0.62,
            "goal_alignment": "medium",
            "reason": "event reason",
            "inspected_error": False,
            "source_state": "test_failed_after_file_edit",
            "risk_hint": "goal_drift_possible",
            "notes": "caller notes",
        },
    )

    metadata = _read_jsonl(hook.trace_path)[0]["metadata"]
    assert metadata["confidence"] == 0.62
    assert metadata["goal_alignment"] == "medium"
    assert metadata["reason"] == "event reason"
    assert metadata["inspected_error"] is False
    assert metadata["source_state"] == "test_failed_after_file_edit"
    assert metadata["risk_hint"] == "goal_drift_possible"
    assert metadata["notes"] == "caller notes"


def test_env_config_helper_is_disabled_without_enabled_env() -> None:
    config = hook_config_from_env({})

    assert config["enabled"] is False
    assert str(config["trace_path"]).endswith("runtime/citta_trials/task_001/citta_trace.jsonl")
    assert config["default_task_id"] is None


def test_env_config_helper_reads_explicit_opt_in() -> None:
    config = hook_config_from_env(
        {
            "HERMES_CITTA_TRACE_ENABLED": "1",
            "HERMES_CITTA_TRACE_PATH": "runtime/citta_trials/task_002/citta_trace.jsonl",
            "HERMES_CITTA_TASK_ID": "task_002",
        }
    )

    assert config["enabled"] is True
    assert str(config["trace_path"]) == "runtime/citta_trials/task_002/citta_trace.jsonl"
    assert config["default_task_id"] == "task_002"


def test_demo_scenario_triggers_goal_drift_and_redirect(tmp_path: Path) -> None:
    trace_path = tmp_path / "citta_trace.jsonl"
    actions_path = tmp_path / "actions.jsonl"
    dashboard_path = tmp_path / "dashboard.html"
    task_id = "hermes_runtime_hook_demo_001"
    hook = HermesRuntimeTraceHook(
        trace_path,
        enabled=True,
        default_task_id=task_id,
        default_metadata={"notes": "unit test demo"},
    )

    hook.record_user_input("Improve UI and keep tests passing")
    hook.record_file_edit(
        "src/ui.py",
        metadata={"confidence": 0.62, "goal_alignment": "medium"},
    )
    hook.record_command_result("python -m pytest", status="failed", error="test_ui_render failed")
    hook.record_file_edit(
        "src/ui.py",
        metadata={
            "confidence": 0.40,
            "goal_alignment": "low",
            "inspected_error": False,
            "risk_hint": "goal_drift_possible",
        },
    )
    hook.record_final_answer("Done")

    report = HermesCittaSkill(trace_path, actions_path, dashboard_path).observe(
        goal="Hermes runtime hook demo",
        task_id=task_id,
    )

    risk_types = {risk["type"] for risk in report["risks"]}
    action_names = {action["action"] for action in report["recommended_actions"]}
    assert {"failed_event_detected", "edit_after_failed_test", "no_test_after_code_edit", "goal_drift_possible"}.issubset(risk_types)
    assert {"inspect_error", "pause", "run_tests", "view_diff", "redirect"}.issubset(action_names)
    assert dashboard_path.exists()
