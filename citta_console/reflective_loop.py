"""Automatic reflective body loop runner.

Runs observe -> record reflection -> reflective body act in a loop until a
safe stop condition is reached. This is rule-based orchestration only.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .body_policy import append_reflective_trace_event
from .observer import observe
from .renderer import render_dashboard
from .trace_reader import events_to_dicts, filter_events_by_task, read_trace

BLOCKING_BODY_ACTIONS = {"pause", "ask_user", "stop"}


def default_reflections_path(trace_path: str | Path) -> Path:
    return Path(trace_path).with_name("reflections.jsonl")


def _applied_reflection_ids(events: list[dict[str, Any]]) -> set[str]:
    applied: set[str] = set()
    for event in events:
        metadata = event.get("metadata")
        if not isinstance(metadata, dict):
            continue
        reflection_id = metadata.get("source_reflection_id")
        if reflection_id:
            applied.add(str(reflection_id))
    return applied


def _load_task_events(trace_path: str | Path, task_id: str) -> list[dict[str, Any]]:
    events = read_trace(trace_path)
    return events_to_dicts(filter_events_by_task(events, task_id))


def run_reflective_tick(
    trace_path: str | Path,
    *,
    task_id: str,
    goal: str | None = None,
    actions_path: str | Path | None = None,
    reflections_path: str | Path | None = None,
    record_reflection: bool = True,
    fallback_action: str = "edit_file",
) -> dict[str, Any]:
    """Run one observe cycle and optionally let the reflective body act once."""

    trace_file = Path(trace_path)
    reflections_file = (
        Path(reflections_path)
        if reflections_path is not None
        else default_reflections_path(trace_file)
    )

    event_dicts = _load_task_events(trace_file, task_id)
    report = observe(
        trace_file,
        task_id=task_id,
        goal=goal,
        actions_path=actions_path,
        reflections_path=reflections_file,
        record_reflection=record_reflection,
    )

    reflection = report.get("reflection") or {}
    reflection_id = reflection.get("reflection_id")
    tick: dict[str, Any] = {
        "action": "observed",
        "report": report,
        "reflection_id": reflection_id,
        "body_event": None,
        "body_action": None,
        "lesson_applied": None,
        "stop_hint": None,
    }

    if report.get("body_loop_status", {}).get("lesson_applied") is True:
        tick["action"] = "already_applied"
        return tick

    if reflection_id and reflection_id in _applied_reflection_ids(event_dicts):
        tick["action"] = "reflection_already_applied"
        return tick

    body_event = append_reflective_trace_event(
        trace_file,
        reflections_file,
        task_id=task_id,
        fallback=fallback_action,
    )
    body_metadata = body_event.get("metadata") or {}
    lesson_applied = body_metadata.get("lesson_applied")
    body_action = body_event.get("action")

    tick.update(
        {
            "action": "acted",
            "body_event": body_event,
            "body_action": body_action,
            "lesson_applied": lesson_applied,
        }
    )

    if body_action in BLOCKING_BODY_ACTIONS or body_event.get("status") == "blocked":
        tick["stop_hint"] = "body_blocked"
    elif lesson_applied is True:
        tick["stop_hint"] = "lesson_applied"

    return tick


def run_reflective_loop(
    trace_path: str | Path,
    *,
    task_id: str,
    goal: str | None = None,
    actions_path: str | Path | None = None,
    reflections_path: str | Path | None = None,
    dashboard_path: str | Path | None = None,
    max_iterations: int = 5,
    record_reflection: bool = True,
    fallback_action: str = "edit_file",
    refresh_interval_seconds: int = 0,
) -> dict[str, Any]:
    """Run the reflective body loop until a stop condition is met."""

    if max_iterations < 1:
        raise ValueError("max_iterations must be >= 1")

    trace_file = Path(trace_path)
    reflections_file = (
        Path(reflections_path)
        if reflections_path is not None
        else default_reflections_path(trace_file)
    )

    steps: list[dict[str, Any]] = []
    stop_reason = "max_iterations"

    for iteration in range(1, max_iterations + 1):
        tick = run_reflective_tick(
            trace_file,
            task_id=task_id,
            goal=goal,
            actions_path=actions_path,
            reflections_path=reflections_file,
            record_reflection=record_reflection,
            fallback_action=fallback_action,
        )

        report = tick["report"]
        step = {
            "iteration": iteration,
            "phase": "act" if tick["action"] == "acted" else "observe",
            "decision": report.get("decision"),
            "body_action": tick.get("body_action"),
            "lesson_applied": tick.get("lesson_applied"),
            "reflection_id": tick.get("reflection_id"),
            "body_status": (tick.get("body_event") or {}).get("status"),
            "tick_action": tick["action"],
        }
        steps.append(step)

        if tick["action"] == "already_applied":
            stop_reason = "lesson_applied"
            break
        if tick["action"] == "reflection_already_applied":
            stop_reason = "reflection_already_applied"
            break
        if tick.get("stop_hint") == "body_blocked":
            stop_reason = "body_blocked"
            break
        if tick.get("stop_hint") == "lesson_applied":
            stop_reason = "lesson_applied"
            break

    final_report = observe(
        trace_file,
        task_id=task_id,
        goal=goal,
        actions_path=actions_path,
        reflections_path=reflections_file,
        record_reflection=False,
    )

    if dashboard_path is not None:
        render_dashboard(
            final_report,
            dashboard_path,
            refresh_interval_seconds=refresh_interval_seconds,
        )

    return {
        "ok": True,
        "task_id": task_id,
        "iterations": len(steps),
        "stop_reason": stop_reason,
        "steps": steps,
        "final_report": final_report,
        "trace_path": str(trace_file),
        "reflections_path": str(reflections_file),
        "dashboard_path": str(dashboard_path) if dashboard_path is not None else None,
    }
