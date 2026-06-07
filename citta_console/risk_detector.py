"""Basic risk detection rules for trace-derived state."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from typing import Any

from .analyzer import EDIT_ACTIONS, TEST_ACTIONS
from .permissions import classify_action
from .schemas import PermissionLevel, Risk, to_dict


def _event_dicts(events: Iterable[dict[str, Any] | object]) -> list[dict[str, Any]]:
    return [to_dict(event) for event in events]


def _is_test(event: dict[str, Any]) -> bool:
    action = str(event.get("action", "")).lower()
    agent = str(event.get("agent", "")).lower()
    target = str(event.get("target", "")).lower()
    return action in TEST_ACTIONS or "test" in action or "test" in agent or "test" in target


def _is_edit(event: dict[str, Any]) -> bool:
    action = str(event.get("action", "")).lower()
    return action in EDIT_ACTIONS or action.endswith("_file")


def _has_inspection_after(events: list[dict[str, Any]], index: int) -> bool:
    return any(
        str(event.get("action", "")).lower() in {"inspect_error", "summarize_state"}
        for event in events[index + 1 :]
    )


def detect_risks(
    events: Iterable[dict[str, Any] | object],
    goal: str | None = None,
    requested_action: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    event_list = _event_dicts(events)
    risks: list[Risk] = []

    failed_events = [event for event in event_list if event.get("status") == "failed"]
    if failed_events:
        latest = failed_events[-1]
        risks.append(
            Risk(
                type="failed_event_detected",
                severity="medium",
                reason=f"{latest.get('agent')} reported failed during {latest.get('action')}.",
                event_id=latest.get("event_id"),
                target=latest.get("target"),
            )
        )

    failure_keys = Counter(
        (
            event.get("agent"),
            event.get("action"),
            event.get("target"),
        )
        for event in failed_events
    )
    if any(count >= 3 for count in failure_keys.values()):
        risks.append(
            Risk(
                type="repeated_failure",
                severity="high",
                reason="The same failure pattern appeared at least three times.",
            )
        )

    failed_test_indices = [
        index
        for index, event in enumerate(event_list)
        if event.get("status") == "failed" and _is_test(event)
    ]
    if failed_test_indices:
        last_failed_test = failed_test_indices[-1]
        if not _has_inspection_after(event_list, last_failed_test) and any(
            _is_edit(event) for event in event_list[last_failed_test + 1 :]
        ):
            risks.append(
                Risk(
                    type="edit_after_failed_test",
                    severity="high",
                    reason="A file was edited after a failed test without inspecting the error.",
                )
            )

    recent_keys = [
        (
            event.get("agent"),
            event.get("action"),
            event.get("target"),
            event.get("status"),
        )
        for event in event_list[-10:]
    ]
    if recent_keys and max(Counter(recent_keys).values()) >= 4:
        risks.append(
            Risk(
                type="loop_detected",
                severity="medium",
                reason="The same action pattern repeated several times in recent trace events.",
            )
        )

    edit_indices = [index for index, event in enumerate(event_list) if _is_edit(event)]
    if edit_indices and not any(_is_test(event) for event in event_list[edit_indices[-1] + 1 :]):
        risks.append(
            Risk(
                type="no_test_after_code_edit",
                severity="medium",
                reason="Code changed and no later test event has been recorded.",
            )
        )

    if requested_action:
        action_name = str(requested_action.get("action", ""))
        level = classify_action(action_name)
        if level in {PermissionLevel.DANGEROUS.value, PermissionLevel.FORBIDDEN.value}:
            risks.append(
                Risk(
                    type="dangerous_action_requested",
                    severity="critical" if level == PermissionLevel.FORBIDDEN.value else "high",
                    reason=f"Requested action '{action_name}' is classified as {level}.",
                    target=requested_action.get("target"),
                )
            )

    if goal:
        low_confidence_events = [
            event
            for event in event_list[-5:]
            if isinstance(event.get("metadata"), dict)
            and event["metadata"].get("confidence") is not None
            and float(event["metadata"].get("confidence", 1.0)) < 0.4
        ]
        if low_confidence_events:
            risks.append(
                Risk(
                    type="goal_drift_possible",
                    severity="low",
                    reason="Recent events report low confidence while a goal is active.",
                )
            )

    return [risk.to_dict() for risk in risks]
