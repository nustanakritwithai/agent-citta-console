"""Long-running reflective body daemon.

Polls trace JSONL for changes and runs observe-reflect-act ticks without
requiring manual demo scripts. Rule-based only; no shell execution.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from .observer import observe
from .reflective_loop import default_reflections_path, run_reflective_tick
from .renderer import render_dashboard
from .trace_reader import events_to_dicts, filter_events_by_task, read_trace


@dataclass(slots=True)
class ReflectiveDaemonState:
    last_trace_mtime: float | None = None
    last_trace_size: int = 0
    last_event_count: int = 0
    ticks_run: int = 0
    idle_polls: int = 0
    blocked: bool = False
    history: list[dict[str, Any]] = field(default_factory=list)


def _trace_snapshot(trace_path: Path, task_id: str) -> tuple[float, int, int]:
    stat = trace_path.stat()
    events = events_to_dicts(
        filter_events_by_task(read_trace(trace_path), task_id)
    )
    return stat.st_mtime, stat.st_size, len(events)


def trace_has_changed(
    trace_path: Path,
    task_id: str,
    state: ReflectiveDaemonState,
) -> bool:
    if not trace_path.exists():
        return False

    mtime, size, event_count = _trace_snapshot(trace_path, task_id)
    if state.last_trace_mtime is None:
        return event_count > 0

    return (
        mtime != state.last_trace_mtime
        or size != state.last_trace_size
        or event_count != state.last_event_count
    )


def update_trace_snapshot(
    trace_path: Path,
    task_id: str,
    state: ReflectiveDaemonState,
) -> None:
    if not trace_path.exists():
        state.last_trace_mtime = None
        state.last_trace_size = 0
        state.last_event_count = 0
        return

    mtime, size, event_count = _trace_snapshot(trace_path, task_id)
    state.last_trace_mtime = mtime
    state.last_trace_size = size
    state.last_event_count = event_count


def should_process_tick(
    trace_path: Path,
    task_id: str,
    state: ReflectiveDaemonState,
) -> bool:
    if state.blocked:
        return trace_has_changed(trace_path, task_id, state)
    return trace_has_changed(trace_path, task_id, state)


def run_reflective_daemon(
    trace_path: str | Path,
    *,
    task_id: str,
    goal: str | None = None,
    actions_path: str | Path | None = None,
    reflections_path: str | Path | None = None,
    dashboard_path: str | Path | None = None,
    poll_interval_seconds: float = 2.0,
    record_reflection: bool = True,
    fallback_action: str = "edit_file",
    refresh_interval_seconds: int = 0,
    max_cycles: int | None = None,
    sleep_fn: Callable[[float], None] = time.sleep,
    should_stop: Callable[[], bool] | None = None,
) -> dict[str, Any]:
    """Poll trace changes and run reflective ticks until stopped."""

    if poll_interval_seconds < 0:
        raise ValueError("poll_interval_seconds must be >= 0")
    if max_cycles is not None and max_cycles < 1:
        raise ValueError("max_cycles must be >= 1 when provided")

    trace_file = Path(trace_path)
    reflections_file = (
        Path(reflections_path)
        if reflections_path is not None
        else default_reflections_path(trace_file)
    )
    state = ReflectiveDaemonState()
    cycles = 0
    stop_reason = "running"

    while True:
        if should_stop and should_stop():
            stop_reason = "stopped"
            break
        if max_cycles is not None and cycles >= max_cycles:
            stop_reason = "max_cycles"
            break

        cycles += 1

        if should_process_tick(trace_file, task_id, state):
            tick = run_reflective_tick(
                trace_file,
                task_id=task_id,
                goal=goal,
                actions_path=actions_path,
                reflections_path=reflections_file,
                record_reflection=record_reflection,
                fallback_action=fallback_action,
            )
            state.ticks_run += 1
            state.blocked = tick.get("stop_hint") == "body_blocked"
            state.history.append(
                {
                    "cycle": cycles,
                    "tick_action": tick["action"],
                    "body_action": tick.get("body_action"),
                    "lesson_applied": tick.get("lesson_applied"),
                    "stop_hint": tick.get("stop_hint"),
                }
            )
            update_trace_snapshot(trace_file, task_id, state)

            if dashboard_path is not None:
                render_dashboard(
                    tick["report"],
                    dashboard_path,
                    refresh_interval_seconds=refresh_interval_seconds,
                )
        else:
            state.idle_polls += 1

        if max_cycles is None or cycles < max_cycles:
            if poll_interval_seconds > 0:
                sleep_fn(poll_interval_seconds)

    final_report = observe(
        trace_file,
        task_id=task_id,
        goal=goal,
        actions_path=actions_path,
        reflections_path=reflections_file,
        record_reflection=False,
    )

    return {
        "ok": True,
        "task_id": task_id,
        "stop_reason": stop_reason,
        "cycles": cycles,
        "ticks_run": state.ticks_run,
        "idle_polls": state.idle_polls,
        "blocked": state.blocked,
        "history": state.history,
        "final_report": final_report,
        "trace_path": str(trace_file),
        "reflections_path": str(reflections_file),
        "dashboard_path": str(dashboard_path) if dashboard_path is not None else None,
        "poll_interval_seconds": poll_interval_seconds,
    }
