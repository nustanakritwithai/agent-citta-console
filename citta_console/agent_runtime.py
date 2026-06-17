"""Default runtime paths and helpers for the always-on agent Citta layer."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .config import CittaConfig, load_config
from .observer import observe
from .reflective_loop import default_reflections_path
from .renderer import render_dashboard
from .skills.hermes_citta_skill.trace_writer import append_citta_event, record_user_input

_PACKAGE_ROOT = Path(__file__).resolve().parent.parent
RUNTIME_DIR = _PACKAGE_ROOT / "runtime" / "citta"
DEFAULT_CONFIG_PATH = RUNTIME_DIR / "citta_config.json"
DEFAULT_TASK_ID = "agent_main"
DEFAULT_AGENT = "cursor_cloud_agent"
DEFAULT_FRAMEWORK = "cursor"


def load_runtime_config(config_path: str | Path | None = None) -> CittaConfig:
    return load_config(config_path or DEFAULT_CONFIG_PATH)


def runtime_paths(config_path: str | Path | None = None) -> dict[str, Path | str]:
    config = load_runtime_config(config_path)
    trace_path = Path(config.trace_path)
    reflections_path = default_reflections_path(trace_path)
    return {
        "config_path": Path(config_path or DEFAULT_CONFIG_PATH),
        "trace_path": trace_path,
        "actions_path": Path(config.actions_path),
        "dashboard_path": Path(config.dashboard_path),
        "reflections_path": reflections_path,
        "goal": config.goal,
        "task_id": DEFAULT_TASK_ID,
        "refresh_interval_seconds": config.refresh_interval_seconds,
    }


def ensure_runtime_layout(config_path: str | Path | None = None) -> dict[str, Path]:
    paths = runtime_paths(config_path)
    trace_path = Path(paths["trace_path"])
    actions_path = Path(paths["actions_path"])
    dashboard_path = Path(paths["dashboard_path"])
    reflections_path = Path(paths["reflections_path"])

    trace_path.parent.mkdir(parents=True, exist_ok=True)
    actions_path.parent.mkdir(parents=True, exist_ok=True)
    dashboard_path.parent.mkdir(parents=True, exist_ok=True)

    for path in (trace_path, actions_path, reflections_path):
        if not path.exists():
            path.touch()

    return {
        "trace_path": trace_path,
        "actions_path": actions_path,
        "dashboard_path": dashboard_path,
        "reflections_path": reflections_path,
    }


def record_agent_event(
    *,
    action: str,
    target: str | None = None,
    status: str = "completed",
    input: str | None = None,
    output: str | None = None,
    error: str | None = None,
    metadata: dict[str, Any] | None = None,
    task_id: str = DEFAULT_TASK_ID,
    config_path: str | Path | None = None,
) -> dict[str, Any]:
    paths = ensure_runtime_layout(config_path)
    merged_metadata = {"source": "agent_runtime", **(metadata or {})}
    return append_citta_event(
        paths["trace_path"],
        task_id=task_id,
        agent=DEFAULT_AGENT,
        framework=DEFAULT_FRAMEWORK,
        action=action,
        target=target,
        status=status,
        input=input,
        output=output,
        error=error,
        metadata=merged_metadata,
    )


def record_user_request(
    content: str,
    *,
    task_id: str = DEFAULT_TASK_ID,
    config_path: str | Path | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    paths = ensure_runtime_layout(config_path)
    merged_metadata = {"source": "agent_runtime", **(metadata or {})}
    return record_user_input(
        paths["trace_path"],
        task_id,
        content,
        metadata=merged_metadata,
    )


def get_runtime_status(
    *,
    task_id: str = DEFAULT_TASK_ID,
    config_path: str | Path | None = None,
    record_reflection: bool = False,
    render_dashboard_file: bool = True,
) -> dict[str, Any]:
    paths = ensure_runtime_layout(config_path)
    config = load_runtime_config(config_path)
    report = observe(
        paths["trace_path"],
        task_id=task_id,
        goal=config.goal,
        actions_path=paths["actions_path"],
        reflections_path=paths["reflections_path"],
        record_reflection=record_reflection,
    )
    if render_dashboard_file:
        render_dashboard(
            report,
            paths["dashboard_path"],
            refresh_interval_seconds=config.refresh_interval_seconds,
        )

    return {
        "ok": True,
        "task_id": task_id,
        "trace_path": str(paths["trace_path"]),
        "reflections_path": str(paths["reflections_path"]),
        "dashboard_path": str(paths["dashboard_path"]),
        "report": report,
    }
