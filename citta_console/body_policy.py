"""Rule-based body agent policy driven by Citta reflections.

Maps reflection recommendations to trace events. This is a functional
policy layer, not consciousness and not self-modifying code.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .reflection import read_reflections
from .schemas import make_id, now_iso


def parse_recommended_action(reflection: dict[str, Any]) -> str:
    """Extract the action name from a reflection next_recommendation field."""

    next_recommendation = str(reflection.get("next_recommendation", "")).strip()
    if ":" in next_recommendation:
        return next_recommendation.split(":", 1)[0].strip()
    return next_recommendation or "continue"


def choose_action_from_reflection(
    reflection: dict[str, Any] | None,
    *,
    fallback: str = "edit_file",
) -> tuple[str, str]:
    """Choose the next body action from the latest reflection."""

    if not reflection:
        return fallback, "No reflection available; using default body behavior."
    action = parse_recommended_action(reflection)
    return action, f"Applied reflection recommendation: {action}"


def is_lesson_applied(reflection: dict[str, Any] | None, chosen_action: str) -> bool:
    """Return whether the chosen action matches the reflection recommendation."""

    if not reflection:
        return False
    return parse_recommended_action(reflection) == chosen_action


def _action_details(action: str, reflection: dict[str, Any] | None) -> dict[str, Any]:
    if action == "inspect_error":
        return {
            "target": "latest_failed_test",
            "status": "completed",
            "output": "Inspected failing test output before making more edits.",
            "error": None,
            "inspected_error": True,
        }
    if action == "ask_user":
        return {
            "target": "user",
            "status": "blocked",
            "output": "Paused to request human input after repeated lessons.",
            "error": None,
        }
    if action == "pause":
        return {
            "target": "agent_runtime",
            "status": "blocked",
            "output": "Paused agents after reflection recommendation.",
            "error": None,
        }
    if action == "run_tests":
        return {
            "target": "python -m pytest",
            "status": "completed",
            "output": "Ran tests after reflection recommendation.",
            "error": None,
        }
    if action == "edit_file":
        return {
            "target": "src/ui.js",
            "status": "completed",
            "output": "Continued editing without applying the reflection lesson.",
            "error": None,
        }
    return {
        "target": reflection.get("task_id") if reflection else "trace.jsonl",
        "status": "completed",
        "output": f"Handled reflective action {action}.",
        "error": None,
    }


def build_reflective_trace_event(
    action: str,
    *,
    task_id: str,
    reflection: dict[str, Any] | None,
    agent: str = "reflective_body_agent",
    reason: str,
) -> dict[str, Any]:
    """Build a trace event that records whether a reflection lesson was applied."""

    details = _action_details(action, reflection)
    metadata: dict[str, Any] = {
        "reflective_body_agent": True,
        "lesson_applied": is_lesson_applied(reflection, action),
        "applied_recommendation": action,
        "reflection_reason": reason,
        "source": "citta_console.body_policy",
    }
    if reflection:
        metadata["source_reflection_id"] = reflection.get("reflection_id")
        metadata["reflection_lesson"] = reflection.get("lesson")
    if details.get("inspected_error"):
        metadata["inspected_error"] = True

    return {
        "time": now_iso(),
        "event_id": make_id("evt"),
        "task_id": task_id,
        "agent": agent,
        "framework": "generic",
        "action": action,
        "target": details["target"],
        "status": details["status"],
        "input": reason,
        "output": details["output"],
        "error": details.get("error"),
        "metadata": metadata,
    }


def extract_body_loop_status(events: list[dict[str, Any]]) -> dict[str, Any]:
    """Read lesson application status from the latest reflective body event."""

    for event in reversed(events):
        metadata = event.get("metadata")
        if not isinstance(metadata, dict):
            continue
        if metadata.get("reflective_body_agent") or metadata.get("lesson_applied") is not None:
            lesson_applied = metadata.get("lesson_applied")
            return {
                "lesson_applied": lesson_applied,
                "applied_recommendation": metadata.get("applied_recommendation"),
                "source_reflection_id": metadata.get("source_reflection_id"),
                "body_agent": event.get("agent"),
                "body_loop_status": (
                    "lesson_applied"
                    if lesson_applied is True
                    else "lesson_not_applied"
                    if lesson_applied is False
                    else "unknown"
                ),
            }

    return {
        "lesson_applied": None,
        "applied_recommendation": None,
        "source_reflection_id": None,
        "body_agent": None,
        "body_loop_status": "no_reflective_body_event",
    }


def latest_reflection_for_task(
    reflections_path: str,
    *,
    task_id: str,
) -> dict[str, Any] | None:
    reflections = read_reflections(reflections_path, task_id=task_id, limit=1)
    return reflections[-1] if reflections else None


def plan_reflective_action(
    reflections_path: str,
    *,
    task_id: str,
    fallback: str = "edit_file",
) -> dict[str, Any]:
    """Plan the next reflective body action without writing a trace event."""

    reflection = latest_reflection_for_task(reflections_path, task_id=task_id)
    action, reason = choose_action_from_reflection(reflection, fallback=fallback)
    return {
        "action": action,
        "reason": reason,
        "reflection": reflection,
        "lesson_applied": is_lesson_applied(reflection, action),
    }


def append_reflective_trace_event(
    trace_path: str | Path,
    reflections_path: str | Path,
    *,
    task_id: str,
    fallback: str = "edit_file",
    agent: str = "reflective_body_agent",
) -> dict[str, Any]:
    """Plan and append a reflective body trace event to JSONL."""

    plan = plan_reflective_action(
        str(reflections_path),
        task_id=task_id,
        fallback=fallback,
    )
    event = build_reflective_trace_event(
        plan["action"],
        task_id=task_id,
        reflection=plan["reflection"],
        agent=agent,
        reason=plan["reason"],
    )
    trace_file = Path(trace_path)
    trace_file.parent.mkdir(parents=True, exist_ok=True)
    with trace_file.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")
    return event
