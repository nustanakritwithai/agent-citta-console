"""Self-reflection trace helpers for the Citta Console.

This module records contextual post-action reflections as JSONL evidence.
It does not claim consciousness, execute commands, or modify agent code.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from .schemas import (
    CittaReflection,
    make_id,
    now_iso,
    to_dict,
    validate_reflection,
)
from .storage import read_jsonl

REFLECTION_AGENT = "citta_observer"

LESSONS_BY_STATE = {
    "no_trace": "Begin recording trace events before reflection can be meaningful.",
    "test_failed_after_file_edit": (
        "Inspect failing test output before making more file edits."
    ),
    "test_failed": "Diagnose the failure before taking further action.",
    "event_failed": "Review the failed event and its error output before continuing.",
    "code_changed_no_test": "Run tests after code changes to catch regressions early.",
    "agent_blocked": "Resolve the blocking condition before resuming work.",
    "agent_running": "Wait for the active action to finish before reflecting again.",
}


def _event_dicts(events: list[dict[str, Any] | object]) -> list[dict[str, Any]]:
    return [to_dict(event) for event in events]


def _describe_last_action(events: list[dict[str, Any]]) -> str:
    if not events:
        return "No action recorded yet."
    last = events[-1]
    agent = str(last.get("agent", "agent"))
    action = str(last.get("action", "acted"))
    target = last.get("target")
    status = str(last.get("status", "unknown"))
    if target:
        return f"{agent} {action} on {target} ({status})"
    return f"{agent} {action} ({status})"


def _describe_result(analysis: dict[str, Any]) -> str:
    current_state = str(analysis.get("current_state", "trace_observed"))
    summary = str(analysis.get("summary", "")).strip()
    if summary:
        return f"{current_state}: {summary}"
    return current_state.replace("_", " ")


def _describe_risk_or_mistake(risks: list[dict[str, Any]]) -> str:
    if not risks:
        return "No significant risk detected in the current trace."
    parts = []
    for risk in risks[:3]:
        risk_type = str(risk.get("type", "risk"))
        reason = str(risk.get("reason", ""))
        parts.append(f"{risk_type}: {reason}" if reason else risk_type)
    return "; ".join(parts)


def _derive_lesson(current_state: str, risks: list[dict[str, Any]]) -> str:
    if current_state in LESSONS_BY_STATE:
        return LESSONS_BY_STATE[current_state]
    risk_types = {str(risk.get("type", "")) for risk in risks}
    if "loop_detected" in risk_types or "repeated_failure" in risk_types:
        return "Break the retry loop and change strategy instead of repeating the same action."
    if "goal_drift_possible" in risk_types:
        return "Re-check whether recent actions still align with the stated goal."
    if "no_test_after_code_edit" in risk_types:
        return "Validate code changes with tests before moving on."
    return "Review trace events and detected risks before the next action."


def _describe_next_recommendation(recommendations: list[dict[str, Any]]) -> str:
    if not recommendations:
        return "continue: No blocking risks were detected."
    first = recommendations[0]
    action = str(first.get("action", "continue"))
    reason = str(first.get("reason", ""))
    return f"{action}: {reason}" if reason else action


def build_reflection(
    events: list[dict[str, Any] | object],
    analysis: dict[str, Any],
    risks: list[dict[str, Any]],
    recommendations: list[dict[str, Any]],
    *,
    task_id: str,
    goal: str | None = None,
    agent: str = REFLECTION_AGENT,
) -> dict[str, Any]:
    """Build a reflection record from an observation snapshot."""

    event_list = _event_dicts(events)
    current_state = str(analysis.get("current_state", "trace_observed"))
    last_event = event_list[-1] if event_list else {}
    first_recommendation = recommendations[0] if recommendations else {}

    reflection = CittaReflection(
        time=now_iso(),
        reflection_id=make_id("ref"),
        task_id=task_id,
        agent=agent,
        goal=goal or "No goal specified",
        action=_describe_last_action(event_list),
        result=_describe_result(analysis),
        risk_or_mistake=_describe_risk_or_mistake(risks),
        lesson=_derive_lesson(current_state, risks),
        next_recommendation=_describe_next_recommendation(recommendations),
        metadata={
            "current_state": current_state,
            "source_event_id": last_event.get("event_id"),
            "recommended_action": first_recommendation.get("action"),
            "risk_count": len(risks),
        },
    )
    return reflection.to_dict()


def write_reflection(
    path: str | Path,
    reflection: Mapping[str, Any] | CittaReflection,
) -> dict[str, Any]:
    """Append a validated reflection record to JSONL."""

    if isinstance(reflection, CittaReflection):
        record = reflection.to_dict()
    else:
        record = validate_reflection(reflection)
    reflection_path = Path(path)
    reflection_path.parent.mkdir(parents=True, exist_ok=True)
    with reflection_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
    return record


def read_reflections(
    path: str | Path,
    *,
    task_id: str | None = None,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """Read recent reflection records from JSONL."""

    reflections = read_jsonl(path)
    if task_id:
        reflections = [
            reflection
            for reflection in reflections
            if reflection.get("task_id") == task_id
        ]
    if limit <= 0:
        return []
    return reflections[-limit:]


def record_reflection_from_observation(
    events: list[dict[str, Any] | object],
    analysis: dict[str, Any],
    risks: list[dict[str, Any]],
    recommendations: list[dict[str, Any]],
    path: str | Path,
    *,
    task_id: str,
    goal: str | None = None,
) -> dict[str, Any]:
    """Build and append a reflection record from an observation snapshot."""

    reflection = build_reflection(
        events,
        analysis,
        risks,
        recommendations,
        task_id=task_id,
        goal=goal,
    )
    return write_reflection(path, reflection)
