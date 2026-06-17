"""High-level trace observation pipeline."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .analyzer import analyze_current_state
from .body_policy import extract_body_loop_status
from .dispatcher import read_actions
from .memory import summarize_reflection_history
from .recommender import recommend_actions
from .reflection import build_reflection, read_reflections, write_reflection
from .reflection_analyzer import analyze_reflection_history, detect_reflection_risks
from .renderer import render_dashboard
from .risk_detector import detect_risks
from .schemas import CittaReport, now_iso, to_dict
from .trace_reader import events_to_dicts, filter_events_by_task, read_trace


def _build_observation(
    event_dicts: list[dict[str, Any]],
    *,
    active_task_id: str,
    goal: str | None,
    recent: list[dict[str, Any]],
    action_history: list[dict[str, Any]],
    reflections_path: str | Path | None,
    record_reflection: bool,
) -> dict[str, Any]:
    analysis = analyze_current_state(event_dicts, goal=goal)

    reflection_history: list[dict[str, Any]] = []
    if reflections_path is not None:
        reflection_history = read_reflections(
            reflections_path,
            task_id=active_task_id,
        )

    reflection_insights = analyze_reflection_history(
        reflection_history,
        events=event_dicts,
        analysis=analysis,
    )
    risks = detect_risks(event_dicts, goal=goal)
    risks.extend(detect_reflection_risks(reflection_insights, event_dicts, analysis))
    recommendations = recommend_actions(analysis, risks, reflection_insights)
    decision = recommendations[0]["action"] if recommendations else "continue"
    reason = recommendations[0]["reason"] if recommendations else "No action needed."

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
        reflection_history = read_reflections(
            reflections_path,
            task_id=active_task_id,
        )
        reflection_insights = analyze_reflection_history(
            reflection_history,
            events=event_dicts,
            analysis=analysis,
        )

    body_loop_status = extract_body_loop_status(event_dicts)

    memory: dict[str, Any] = {
        "prior_lessons": [],
        "cross_task_lessons": [],
        "memory_summary": "No prior lessons recorded in reflection history.",
    }
    if reflections_path is not None:
        memory = summarize_reflection_history(
            reflections_path,
            task_id=active_task_id,
        )

    return CittaReport(
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
        reflection_insights=reflection_insights,
        body_loop_status=body_loop_status,
        prior_lessons=memory["prior_lessons"],
        cross_task_lessons=memory["cross_task_lessons"],
        memory_summary=memory["memory_summary"],
    ).to_dict()


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
    action_history = (
        read_actions(actions_path, task_id=active_task_id if task_id else None)
        if actions_path
        else []
    )

    return _build_observation(
        event_dicts,
        active_task_id=active_task_id,
        goal=goal,
        recent=recent,
        action_history=action_history,
        reflections_path=reflections_path,
        record_reflection=record_reflection,
    )


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
    action_history = [to_dict(action) for action in adapter.read_actions()]
    if task_id:
        action_history = [
            action for action in action_history if action.get("task_id") == active_task_id
        ]

    report = _build_observation(
        event_dicts,
        active_task_id=active_task_id,
        goal=goal,
        recent=recent,
        action_history=action_history[-limit:],
        reflections_path=reflections_path,
        record_reflection=record_reflection,
    )

    if dashboard_path is not None:
        render_dashboard(
            report,
            dashboard_path,
            refresh_interval_seconds=refresh_interval_seconds,
        )
    return report
