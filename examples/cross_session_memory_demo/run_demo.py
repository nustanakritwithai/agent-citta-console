"""Demonstrate cross-session memory from prior reflection JSONL history."""

from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from citta_console.config import load_config
from citta_console.memory import bootstrap_task_memory, summarize_reflection_history
from citta_console.observer import observe
from citta_console.renderer import render_dashboard
from citta_console.tools import dispatch_tool

DEMO_DIR = Path(__file__).resolve().parent
CONFIG_PATH = DEMO_DIR / "citta_config.json"
NEW_TASK_ID = "dashboard_refresh_003"


def main() -> None:
    config = load_config(str(CONFIG_PATH))
    reflections_path = DEMO_DIR / "reflections.jsonl"
    trace_path = DEMO_DIR / "trace.jsonl"
    dashboard_path = DEMO_DIR / "dashboard.html"

    print("Cross-Session Memory demo")
    print("=" * 40)

    tool_result = dispatch_tool(
        "citta.summarize_reflections",
        {
            "reflections_path": str(reflections_path),
            "task_id": NEW_TASK_ID,
        },
    )
    print("Tool bootstrap:")
    print(json.dumps(tool_result["memory"]["memory_summary"], ensure_ascii=False, indent=2))
    print()

    bootstrap = bootstrap_task_memory(reflections_path, task_id=NEW_TASK_ID)
    print("Bootstrap payload:")
    print(json.dumps(bootstrap, indent=2, ensure_ascii=False))
    print()

    report = observe(
        trace_path,
        goal=config.goal,
        task_id=NEW_TASK_ID,
        reflections_path=reflections_path,
    )
    render_dashboard(report, dashboard_path, refresh_interval_seconds=0)

    print("Observe report memory fields:")
    print(f"  prior_lessons: {len(report['prior_lessons'])}")
    print(f"  cross_task_lessons: {len(report['cross_task_lessons'])}")
    print(f"  memory_summary: {report['memory_summary']}")
    print()
    print(f"Dashboard: {dashboard_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
