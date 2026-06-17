"""High-level trace observation pipeline."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .analyzer import analyze_current_state
from .dispatcher import read_actions
from .recommender import recommend_actions
from .reflection import build_reflection, read_reflections, write_reflection
from .renderer import render_dashboard
from .risk_detector import detect_risks
from .schemas import CittaReport, now_iso, to_dict
from .trace_reader import events_to_dicts, filter_events_by_task, read_trace


def observe(
    trace_path: str | Path,
    *,
    task_id: str | None = None,
    goal: str | None = None,
    actions_path: str | Path | None = None,
    reflections_path: str | Path | None = None,
    record_reflection: bool = False,
    limit: int = 20,
) -> dict[str, Any]:
    events = read_trace(trace_path)
    if task_id:
        events = filter_events_by_task(events, task_id)
    event_dicts = events_to_dicts(events)
    recent = event_dicts[-limit:]
    active_task_id = task_id or (event_dicts[-1]["task_id"] if event_dicts else "default")

    analysis = analyze_current_state(event_dicts, goal=goal)
    risks = detect_risks(event_dicts, goal=goal)
    recommendations = recommend_actions(analysis, risks)
    decision = recommendations[0]["action"] if recommendations else "continue"
    reason = recommendations[0]["reason"] if recommendations else "No action needed."
    action_history = (
        read_actions(actions_path, task_id=active_task_id if task_id else None)
        if actions_path
        else []
    )

    reflection = build_reflection(
        event_dicts,
        analysis,
        risks,
        recommendations,
        task_id=active_task_id,
        goal=goal,
    )
    if record_reflection and reflections_path is not None:
        write_reflection(reflections_path, reflection)

    reflection_history: list[dict[str, Any]] = []
    if reflections_path is not None:
        reflection_history = read_reflections(
            reflections_path,
            task_id=active_task_id if task_id else None,
        )

    report = CittaReport(
        time=now_iso(),
        task_id=active_task_id,
        current_state=analysis["current_state"],
        active_agents=analysis["active_agents"],
        recent_events=len(recent),
        risks=risks,
        recommended_actions=recommendations,
        decision=decision,
        reason=reason,
        summary=analysis["summary"],
        events=recent,
        action_history=action_history,
        goal=goal,
        reflection=reflection,
        reflection_history=reflection_history,
    )
    return report.to_dict()


def observe_with_adapter(
    adapter: Any,
    dashboard_path: str | Path | None = None,
    *,
    goal: str | None = None,
    task_id: str | None = None,
    reflections_path: str | Path | None = None,
    record_reflection: bool = False,
    limit: int = 20,
    refresh_interval_seconds: int = 0,
) -> dict[str, Any]:
    """Build a Citta report from an adapter and optionally render a dashboard."""

    events = adapter.read_events()
    if task_id:
        events = filter_events_by_task(events, task_id)
    event_dicts = events_to_dicts(events)
    recent = event_dicts[-limit:]
    active_task_id = task_id or (event_dicts[-1]["task_id"] if event_dicts else "default")

    analysis = analyze_current_state(event_dicts, goal=goal)
    risks = detect_risks(event_dicts, goal=goal)
    recommendations = recommend_actions(analysis, risks)
    decision = recommendations[0]["action"] if recommendations else "continue"
    reason = recommendations[0]["reason"] if recommendations else "No action needed."
    action_history = [to_dict(action) for action in adapter.read_actions()]
    if task_id:
        action_history = [
            action for action in action_history if action.get("task_id") == active_task_id
        ]

    reflection = build_reflection(
        event_dicts,
        analysis,
        risks,
        recommendations,
        task_id=active_task_id,
        goal=goal,
    )
    if record_reflection and reflections_path is not None:
        write_reflection(reflections_path, reflection)

    reflection_history: list[dict[str, Any]] = []
    if reflections_path is not None:
        reflection_history = read_reflections(
            reflections_path,
            task_id=active_task_id if task_id else None,
        )

    report = CittaReport(
        time=now_iso(),
        task_id=active_task_id,
        current_state=analysis["current_state"],
        active_agents=analysis["active_agents"],
        recent_events=len(recent),
        risks=risks,
        recommended_actions=recommendations,
        decision=decision,
        reason=reason,
        summary=analysis["summary"],
        events=recent,
        action_history=action_history[-limit:],
        goal=goal,
        reflection=reflection,
        reflection_history=reflection_history,
    ).to_dict()

    if dashboard_path is not None:
        render_dashboard(
            report,
            dashboard_path,
            refresh_interval_seconds=refresh_interval_seconds,
        )
    return report
