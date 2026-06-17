"""Analyze reflection history for lesson patterns and reflection-derived risks."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from typing import Any

from .schemas import Risk, to_dict

REPEATED_LESSON_THRESHOLD = 3
SAME_MISTAKE_THRESHOLD = 2

PROBLEMATIC_STATES = {
    "test_failed_after_file_edit",
    "test_failed",
    "event_failed",
    "code_changed_no_test",
    "agent_blocked",
}


def _reflection_dicts(reflections: Iterable[dict[str, Any] | object]) -> list[dict[str, Any]]:
    return [to_dict(reflection) for reflection in reflections]


def _normalize_text(value: Any) -> str:
    return str(value or "").strip().lower()


def _mistake_signatures(risk_or_mistake: str) -> list[str]:
    parts = [part.strip() for part in risk_or_mistake.split(";") if part.strip()]
    signatures: list[str] = []
    for part in parts:
        if ":" in part:
            signatures.append(part.split(":", 1)[0].strip())
        else:
            signatures.append(part)
    return signatures


def _primary_mistake(reflection: dict[str, Any]) -> str:
    signatures = _mistake_signatures(str(reflection.get("risk_or_mistake", "")))
    if signatures:
        return signatures[0]
    return _normalize_text(reflection.get("risk_or_mistake"))


def _recommended_action(reflection: dict[str, Any]) -> str:
    next_recommendation = str(reflection.get("next_recommendation", ""))
    if ":" in next_recommendation:
        return next_recommendation.split(":", 1)[0].strip()
    return next_recommendation.strip()


def _behavior_still_problematic(
    events: list[dict[str, Any]] | None,
    analysis: dict[str, Any] | None,
) -> bool:
    if analysis and analysis.get("current_state") in PROBLEMATIC_STATES:
        return True
    if not events:
        return False

    failed_test_indices = [
        index
        for index, event in enumerate(events)
        if event.get("status") == "failed"
        and "test" in str(event.get("action", "")).lower()
    ]
    if not failed_test_indices:
        return False

    last_failed_test = failed_test_indices[-1]
    later_events = events[last_failed_test + 1 :]
    if not later_events:
        return False

    edit_actions = {"edit_file", "write_file", "create_file", "modify_file"}
    for event in later_events:
        action = str(event.get("action", "")).lower()
        if action in edit_actions or action.endswith("_file"):
            return True
    return False


def analyze_reflection_history(
    reflections: Iterable[dict[str, Any] | object],
    events: list[dict[str, Any]] | None = None,
    analysis: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Summarize lesson and mistake patterns from reflection JSONL history."""

    reflection_list = _reflection_dicts(reflections)
    if not reflection_list:
        return {
            "total_reflections": 0,
            "repeated_lessons": [],
            "most_repeated_lesson": None,
            "most_repeated_lesson_count": 0,
            "repeated_mistakes": [],
            "most_repeated_mistake": None,
            "most_repeated_mistake_count": 0,
            "repeated_lesson_ignored": False,
            "latest_recommended_actions": [],
        }

    lesson_counts = Counter(_normalize_text(item.get("lesson")) for item in reflection_list)
    mistake_counts = Counter(_primary_mistake(item) for item in reflection_list)

    most_repeated_lesson, lesson_count = lesson_counts.most_common(1)[0]
    most_repeated_mistake, mistake_count = mistake_counts.most_common(1)[0]

    repeated_lesson_ignored = (
        lesson_count >= REPEATED_LESSON_THRESHOLD
        and most_repeated_lesson
        and _behavior_still_problematic(events, analysis)
    )

    return {
        "total_reflections": len(reflection_list),
        "repeated_lessons": [
            {"lesson": lesson, "count": count}
            for lesson, count in lesson_counts.most_common()
            if count >= 2
        ],
        "most_repeated_lesson": most_repeated_lesson or None,
        "most_repeated_lesson_count": lesson_count,
        "repeated_mistakes": [
            {"mistake": mistake, "count": count}
            for mistake, count in mistake_counts.most_common()
            if count >= SAME_MISTAKE_THRESHOLD
        ],
        "most_repeated_mistake": most_repeated_mistake or None,
        "most_repeated_mistake_count": mistake_count,
        "repeated_lesson_ignored": repeated_lesson_ignored,
        "latest_recommended_actions": [
            _recommended_action(item) for item in reflection_list[-5:]
        ],
    }


def detect_reflection_risks(
    insights: dict[str, Any],
    events: list[dict[str, Any]] | None = None,
    analysis: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Detect risks derived from reflection history rather than trace alone."""

    if insights.get("total_reflections", 0) == 0:
        return []

    risks: list[Risk] = []

    if insights.get("most_repeated_mistake_count", 0) >= SAME_MISTAKE_THRESHOLD:
        risks.append(
            Risk(
                type="same_mistake_twice",
                severity="high",
                reason=(
                    "The same mistake pattern appeared in multiple reflections: "
                    f"{insights.get('most_repeated_mistake')}."
                ),
                metadata={
                    "count": insights.get("most_repeated_mistake_count"),
                    "mistake": insights.get("most_repeated_mistake"),
                },
            )
        )

    if insights.get("repeated_lesson_ignored"):
        risks.append(
            Risk(
                type="repeated_lesson_ignored",
                severity="high",
                reason=(
                    "The same lesson was recorded at least three times, but the "
                    "trace still shows the problematic behavior."
                ),
                metadata={
                    "lesson": insights.get("most_repeated_lesson"),
                    "count": insights.get("most_repeated_lesson_count"),
                },
            )
        )
    elif (
        insights.get("most_repeated_lesson_count", 0) >= REPEATED_LESSON_THRESHOLD
        and _behavior_still_problematic(events, analysis)
    ):
        risks.append(
            Risk(
                type="repeated_lesson_ignored",
                severity="high",
                reason=(
                    "A lesson repeated across reflections without a change in behavior."
                ),
                metadata={
                    "lesson": insights.get("most_repeated_lesson"),
                    "count": insights.get("most_repeated_lesson_count"),
                },
            )
        )

    return [risk.to_dict() for risk in risks]
