"""Tests for the always-on agent Citta runtime helpers."""

from __future__ import annotations

import json
from pathlib import Path

from citta_console.agent_runtime import (
    DEFAULT_TASK_ID,
    ensure_runtime_layout,
    get_runtime_status,
    record_agent_event,
    record_user_request,
    runtime_paths,
)


def _write_runtime_config(tmp_path: Path) -> Path:
    runtime_dir = tmp_path / "runtime" / "citta"
    runtime_dir.mkdir(parents=True)
    config_path = runtime_dir / "citta_config.json"
    config_path.write_text(
        json.dumps(
            {
                "trace_path": str(runtime_dir / "trace.jsonl"),
                "actions_path": str(runtime_dir / "actions.jsonl"),
                "dashboard_path": str(runtime_dir / "dashboard.html"),
                "refresh_interval_seconds": 0,
                "goal": "Test agent runtime",
            }
        ),
        encoding="utf-8",
    )
    return config_path


def test_ensure_runtime_layout_creates_files(tmp_path: Path) -> None:
    config_path = _write_runtime_config(tmp_path)
    paths = ensure_runtime_layout(config_path)

    for key in ("trace_path", "actions_path", "reflections_path"):
        assert paths[key].exists()
    assert paths["dashboard_path"].parent.exists()


def test_record_agent_event_appends_trace(tmp_path: Path) -> None:
    config_path = _write_runtime_config(tmp_path)
    event = record_agent_event(
        action="shell",
        target="pytest",
        output="109 passed",
        config_path=config_path,
    )

    assert event["agent"] == "cursor_cloud_agent"
    assert event["task_id"] == DEFAULT_TASK_ID
    trace = (tmp_path / "runtime" / "citta" / "trace.jsonl").read_text(encoding="utf-8")
    assert "pytest" in trace


def test_record_user_request_appends_trace(tmp_path: Path) -> None:
    config_path = _write_runtime_config(tmp_path)
    event = record_user_request("Run Citta continuously", config_path=config_path)

    assert event["agent"] == "user"
    trace = (tmp_path / "runtime" / "citta" / "trace.jsonl").read_text(encoding="utf-8")
    assert "Run Citta continuously" in trace


def test_get_runtime_status_renders_dashboard(tmp_path: Path) -> None:
    config_path = _write_runtime_config(tmp_path)
    record_user_request("hello", config_path=config_path)

    status = get_runtime_status(config_path=config_path)
    paths = runtime_paths(config_path)

    assert status["ok"] is True
    assert status["report"]["task_id"] == DEFAULT_TASK_ID
    assert Path(paths["dashboard_path"]).exists()
