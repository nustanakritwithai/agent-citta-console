from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from citta_console.skills.hermes_citta_skill import HermesCittaSkill, HermesRuntimeTraceHook

TASK_ID = "hermes_runtime_hook_demo_001"
BASE = Path(__file__).resolve().parent
TRACE_PATH = BASE / "citta_trace.jsonl"
ACTIONS_PATH = BASE / "actions.jsonl"
DASHBOARD_PATH = BASE / "dashboard.html"
GOAL = "Hermes runtime hook demo"


def main() -> int:
    TRACE_PATH.write_text("", encoding="utf-8")
    ACTIONS_PATH.write_text("", encoding="utf-8")

    hook = HermesRuntimeTraceHook(
        TRACE_PATH,
        enabled=True,
        default_task_id=TASK_ID,
        default_metadata={"notes": "controlled Hermes runtime hook demo"},
    )

    hook.record_user_input("Improve UI and keep tests passing")
    hook.record_file_edit(
        "src/ui.py",
        output="Initial UI edit recorded",
        metadata={"confidence": 0.62, "goal_alignment": "medium"},
    )
    hook.record_command_result(
        "python -m pytest",
        status="failed",
        error="test_ui_render failed",
        metadata={"source_state": "test_failed_after_file_edit"},
    )
    hook.record_file_edit(
        "src/ui.py",
        output="Second edit after failed test recorded",
        metadata={
            "confidence": 0.40,
            "goal_alignment": "low",
            "inspected_error": False,
            "risk_hint": "goal_drift_possible",
            "reason": "continued UI edit after failed test without inspecting error",
        },
    )
    hook.record_final_answer(
        "Demo finished: recommended actions are reported only, not executed.",
        metadata={"notes": "final answer recorded by runtime hook demo"},
    )

    skill = HermesCittaSkill(TRACE_PATH, ACTIONS_PATH, DASHBOARD_PATH)
    report = skill.observe(goal=GOAL, task_id=TASK_ID)
    risks = [risk["type"] for risk in report.get("risks", [])]
    actions = [action["action"] for action in report.get("recommended_actions", [])]

    print(f"Dashboard: {DASHBOARD_PATH}")
    print("Detected risks:")
    for risk in risks:
        print(f"- {risk}")
    print("Recommended actions:")
    for action in actions:
        print(f"- {action}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
