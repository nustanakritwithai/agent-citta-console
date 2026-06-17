from __future__ import annotations

import json
from pathlib import Path

from citta_console.memory import bootstrap_task_memory, summarize_reflection_history
from citta_console.observer import observe
from citta_console.tools import dispatch_tool


LESSON_A = "Inspect failing test output before making more file edits."
LESSON_B = "Run tests after code changes to catch regressions early."


def _write_reflections(path: Path) -> None:
    records = [
        {
            "time": "2026-06-06T09:00:00+07:00",
            "reflection_id": "ref_old_001",
            "task_id": "task_old",
            "goal": "Keep tests passing",
            "action": "code_agent edit_file",
            "result": "test_failed_after_file_edit",
            "risk_or_mistake": "edit_after_failed_test: edits continued.",
            "lesson": LESSON_A,
            "next_recommendation": "inspect_error: inspect first",
            "agent": "citta_observer",
        },
        {
            "time": "2026-06-06T09:05:00+07:00",
            "reflection_id": "ref_old_002",
            "task_id": "task_old",
            "goal": "Keep tests passing",
            "action": "code_agent edit_file",
            "result": "test_failed_after_file_edit",
            "risk_or_mistake": "edit_after_failed_test: edits continued.",
            "lesson": LESSON_A,
            "next_recommendation": "inspect_error: inspect first",
            "agent": "citta_observer",
        },
        {
            "time": "2026-06-06T10:00:00+07:00",
            "reflection_id": "ref_old_003",
            "task_id": "task_api",
            "goal": "Fix API regression",
            "action": "code_agent edit_file",
            "result": "code_changed_no_test",
            "risk_or_mistake": "no_test_after_code_edit: no test recorded.",
            "lesson": LESSON_B,
            "next_recommendation": "run_tests: run tests",
            "agent": "citta_observer",
        },
    ]
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, sort_keys=True) + "\n")


def test_summarize_reflection_history_groups_prior_lessons(tmp_path: Path) -> None:
    reflections = tmp_path / "reflections.jsonl"
    _write_reflections(reflections)

    memory = summarize_reflection_history(reflections, task_id="task_old")

    assert memory["total_reflections"] == 3
    assert memory["task_reflections"] == 2
    assert memory["prior_lessons"][0]["lesson"] == LESSON_A
    assert memory["prior_lessons"][0]["count"] == 2
    assert len(memory["cross_task_lessons"]) == 1
    assert memory["cross_task_lessons"][0]["lesson"] == LESSON_B


def test_bootstrap_task_memory_returns_cross_session_payload(tmp_path: Path) -> None:
    reflections = tmp_path / "reflections.jsonl"
    _write_reflections(reflections)

    bootstrap = bootstrap_task_memory(reflections, task_id="task_new")

    assert bootstrap["task_id"] == "task_new"
    assert bootstrap["prior_lessons"] == []
    assert len(bootstrap["cross_task_lessons"]) == 2
    assert "Cross-task lessons to remember" in bootstrap["memory_summary"]


def test_observe_attaches_prior_lessons_and_memory_summary(tmp_path: Path) -> None:
    reflections = tmp_path / "reflections.jsonl"
    trace = tmp_path / "trace.jsonl"
    _write_reflections(reflections)
    trace.write_text("", encoding="utf-8")

    report = observe(
        trace,
        task_id="task_new",
        goal="Start safely",
        reflections_path=reflections,
    )

    assert report["prior_lessons"] == []
    assert len(report["cross_task_lessons"]) == 2
    assert "Cross-task lessons to remember" in report["memory_summary"]


def test_summarize_reflections_tool_works(tmp_path: Path) -> None:
    reflections = tmp_path / "reflections.jsonl"
    _write_reflections(reflections)

    result = dispatch_tool(
        "citta.summarize_reflections",
        {"reflections_path": str(reflections), "task_id": "task_new"},
    )

    assert result["ok"] is True
    assert result["memory"]["total_reflections"] == 3
    assert "memory_summary" in result["memory"]


def test_memory_summary_includes_task_specific_lessons(tmp_path: Path) -> None:
    reflections = tmp_path / "reflections.jsonl"
    _write_reflections(reflections)

    memory = summarize_reflection_history(reflections, task_id="task_api")

    assert memory["prior_lessons"][0]["lesson"] == LESSON_B
    assert LESSON_A in memory["memory_summary"]
    assert "task_api" in memory["memory_summary"]
