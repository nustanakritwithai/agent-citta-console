"""Recommend next actions from analyzed state and risk signals."""

from __future__ import annotations

from typing import Any

from .schemas import RecommendedAction


ACTION_LABELS = {
    "continue": "Continue",
    "pause": "Pause Agents",
    "stop": "Stop",
    "inspect_error": "Inspect Error",
    "run_tests": "Run Tests",
    "view_diff": "View Diff",
    "summarize_state": "Summarize State",
    "ask_user": "Ask User",
    "redirect": "Redirect Task",
    "rollback": "Rollback",
    "approve": "Approve",
    "reject": "Reject",
}

ACTION_PERMISSIONS = {
    "continue": "safe",
    "inspect_error": "safe",
    "view_diff": "safe",
    "summarize_state": "safe",
    "run_tests": "medium",
    "ask_user": "medium",
    "redirect": "medium",
    "pause": "medium",
    "rollback": "medium",
    "approve": "medium",
    "reject": "medium",
    "stop": "dangerous",
}


def _add(
    actions: list[RecommendedAction],
    action: str,
    reason: str,
    target: str | None = None,
) -> None:
    if any(item.action == action for item in actions):
        return
    actions.append(
        RecommendedAction(
            action=action,
            label=ACTION_LABELS.get(action, action.replace("_", " ").title()),
            permission_level=ACTION_PERMISSIONS.get(action, "safe"),
            reason=reason,
            target=target,
        )
    )


def recommend_actions(
    analysis: dict[str, Any],
    risks: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    risks = risks or []
    current_state = analysis.get("current_state", "trace_observed")
    risk_types = {risk.get("type") for risk in risks}
    recommendations: list[RecommendedAction] = []

    if "edit_after_failed_test" in risk_types or current_state == "test_failed_after_file_edit":
        _add(recommendations, "inspect_error", "A test failed and edits continued afterward.")
        _add(recommendations, "pause", "Pause before more edits hide the root cause.")
    if "failed_event_detected" in risk_types or current_state in {"test_failed", "event_failed"}:
        _add(recommendations, "inspect_error", "A failed event needs diagnosis.")
    if "no_test_after_code_edit" in risk_types or current_state == "code_changed_no_test":
        _add(recommendations, "run_tests", "Code changed without a later test event.")
        _add(recommendations, "view_diff", "Review file changes before continuing.")
    if "repeated_failure" in risk_types or "loop_detected" in risk_types:
        _add(recommendations, "pause", "Repeated failures or loop-like activity were detected.")
        _add(recommendations, "ask_user", "Human input may be needed to break the loop.")
    if "goal_drift_possible" in risk_types:
        _add(recommendations, "redirect", "Re-anchor the active agents to the goal.")
    if "dangerous_action_requested" in risk_types:
        _add(recommendations, "summarize_state", "Review context before approving a risky action.")
        _add(recommendations, "reject", "Reject the unsafe action if it is not necessary.")

    if not recommendations:
        if current_state == "no_trace":
            _add(recommendations, "summarize_state", "No trace exists yet; describe the current state.")
        else:
            _add(recommendations, "continue", "No blocking risks were detected.")

    return [action.to_dict() for action in recommendations]
