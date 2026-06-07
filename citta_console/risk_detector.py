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
        or (
            isinstance(event.get("metadata"), dict)
            and event["metadata"].get("inspected_error") is True
        )
        for event in events[index + 1 :]
    )


def _metadata(event: dict[str, Any]) -> dict[str, Any]:
    metadata = event.get("metadata")
    return metadata if isinstance(metadata, dict) else {}


def _confidence(metadata: dict[str, Any]) -> float | None:
    value = metadata.get("confidence")
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _is_low_goal_alignment(metadata: dict[str, Any]) -> bool:
    value = metadata.get("goal_alignment")
    if isinstance(value, str):
        return value.lower() in {"low", "poor", "weak", "misaligned", "off_goal"}
    try:
        return value is not None and float(value) <= 0.45
    except (TypeError, ValueError):
        return False


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
        goal_drift_events = []
        for event in event_list[-5:]:
            metadata = _metadata(event)
            confidence = _confidence(metadata)
            low_confidence = confidence is not None and confidence <= 0.45
            low_goal_alignment = _is_low_goal_alignment(metadata)
            explicit_hint = metadata.get("risk_hint") == "goal_drift_possible"
            if low_confidence or low_goal_alignment or explicit_hint:
                goal_drift_events.append(event)

        if goal_drift_events:
            latest = goal_drift_events[-1]
            metadata = _metadata(latest)
            risks.append(
                Risk(
                    type="goal_drift_possible",
                    severity="low",
                    reason=(
                        "Recent events report low confidence, low goal alignment, "
                        "or an explicit goal-drift hint while a goal is active."
                    ),
                    event_id=latest.get("event_id"),
                    target=latest.get("target"),
                    metadata={
                        key: metadata[key]
                        for key in ("confidence", "goal_alignment", "reason", "source_state", "risk_hint")
                        if key in metadata
                    },
                )
            )

    return [risk.to_dict() for risk in risks]
