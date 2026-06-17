"""Cross-session memory helpers derived from reflection JSONL history.

This module summarizes prior lessons and mistakes so a new task/session can
bootstrap from external evidence. It does not claim consciousness or modify code.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .reflection_analyzer import _normalize_text, _primary_mistake
from .storage import read_jsonl

DEFAULT_PRIOR_LESSON_LIMIT = 5
DEFAULT_PRIOR_MISTAKE_LIMIT = 5


def _load_reflections(reflections_path: str | Path) -> list[dict[str, Any]]:
    return read_jsonl(reflections_path)


def _lesson_entries(reflections: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}
    for reflection in reflections:
        lesson = str(reflection.get("lesson", "")).strip()
        if not lesson:
            continue
        key = _normalize_text(lesson)
        entry = grouped.setdefault(
            key,
            {
                "lesson": lesson,
                "count": 0,
                "last_seen": reflection.get("time"),
                "task_ids": set(),
            },
        )
        entry["count"] += 1
        entry["last_seen"] = reflection.get("time")
        task_id = reflection.get("task_id")
        if task_id:
            entry["task_ids"].add(str(task_id))

    results = []
    for entry in grouped.values():
        results.append(
            {
                "lesson": entry["lesson"],
                "count": entry["count"],
                "last_seen": entry["last_seen"],
                "task_ids": sorted(entry["task_ids"]),
            }
        )
    results.sort(key=lambda item: (-item["count"], str(item["last_seen"])))
    return results


def _mistake_entries(reflections: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}
    for reflection in reflections:
        mistake = _primary_mistake(reflection)
        if not mistake:
            continue
        key = _normalize_text(mistake)
        entry = grouped.setdefault(
            key,
            {
                "mistake": mistake,
                "count": 0,
                "last_seen": reflection.get("time"),
                "task_ids": set(),
            },
        )
        entry["count"] += 1
        entry["last_seen"] = reflection.get("time")
        task_id = reflection.get("task_id")
        if task_id:
            entry["task_ids"].add(str(task_id))

    results = []
    for entry in grouped.values():
        results.append(
            {
                "mistake": entry["mistake"],
                "count": entry["count"],
                "last_seen": entry["last_seen"],
                "task_ids": sorted(entry["task_ids"]),
            }
        )
    results.sort(key=lambda item: (-item["count"], str(item["last_seen"])))
    return results


def build_memory_summary_text(
    prior_lessons: list[dict[str, Any]],
    *,
    task_id: str | None = None,
    cross_task_lessons: list[dict[str, Any]] | None = None,
) -> str:
    if not prior_lessons and not cross_task_lessons:
        return "No prior lessons recorded in reflection history."

    parts: list[str] = []
    if task_id and prior_lessons:
        parts.append(f"Prior lessons for task {task_id}:")
        for item in prior_lessons[:DEFAULT_PRIOR_LESSON_LIMIT]:
            parts.append(f"- {item['lesson']} (seen {item['count']} times)")
    elif prior_lessons:
        parts.append("Prior lessons from reflection history:")
        for item in prior_lessons[:DEFAULT_PRIOR_LESSON_LIMIT]:
            parts.append(f"- {item['lesson']} (seen {item['count']} times)")

    if cross_task_lessons:
        parts.append("Cross-task lessons to remember:")
        for item in cross_task_lessons[:DEFAULT_PRIOR_LESSON_LIMIT]:
            tasks = ", ".join(item.get("task_ids", []))
            parts.append(f"- {item['lesson']} (from tasks: {tasks or 'unknown'})")

    return " ".join(parts)


def summarize_reflection_history(
    reflections_path: str | Path,
    *,
    task_id: str | None = None,
    lesson_limit: int = DEFAULT_PRIOR_LESSON_LIMIT,
    mistake_limit: int = DEFAULT_PRIOR_MISTAKE_LIMIT,
) -> dict[str, Any]:
    """Summarize lessons and mistakes for cross-session bootstrap."""

    all_reflections = _load_reflections(reflections_path)
    task_reflections = (
        [item for item in all_reflections if item.get("task_id") == task_id]
        if task_id
        else all_reflections
    )

    prior_lessons = _lesson_entries(task_reflections)[:lesson_limit]
    top_mistakes = _mistake_entries(task_reflections)[:mistake_limit]

    cross_task_lessons: list[dict[str, Any]] = []
    if task_id:
        other_reflections = [
            item for item in all_reflections if item.get("task_id") != task_id
        ]
        cross_task_lessons = _lesson_entries(other_reflections)[:lesson_limit]

    tasks_seen = sorted(
        {
            str(item.get("task_id"))
            for item in all_reflections
            if item.get("task_id")
        }
    )

    return {
        "total_reflections": len(all_reflections),
        "task_reflections": len(task_reflections),
        "tasks_seen": tasks_seen,
        "prior_lessons": prior_lessons,
        "top_mistakes": top_mistakes,
        "cross_task_lessons": cross_task_lessons,
        "memory_summary": build_memory_summary_text(
            prior_lessons,
            task_id=task_id,
            cross_task_lessons=cross_task_lessons,
        ),
    }


def bootstrap_task_memory(
    reflections_path: str | Path,
    *,
    task_id: str,
) -> dict[str, Any]:
    """Return cross-session memory payload for a task bootstrap."""

    memory = summarize_reflection_history(reflections_path, task_id=task_id)
    return {
        "task_id": task_id,
        "prior_lessons": memory["prior_lessons"],
        "cross_task_lessons": memory["cross_task_lessons"],
        "top_mistakes": memory["top_mistakes"],
        "memory_summary": memory["memory_summary"],
        "tasks_seen": memory["tasks_seen"],
    }
