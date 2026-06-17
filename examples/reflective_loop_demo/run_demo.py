"""Run the reflective body agent loop demo.

Flow:
1. Body leaves a problematic trace (edit -> failed test -> edit)
2. Citta observes and records a reflection
3. Reflective body agent reads the reflection and changes behavior
4. Citta observes again and reports lesson_applied on the dashboard
"""

from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from citta_console.body_policy import append_reflective_trace_event
from citta_console.config import load_config
from citta_console.observer import observe
from citta_console.renderer import render_dashboard

DEMO_DIR = Path(__file__).resolve().parent
CONFIG_PATH = DEMO_DIR / "citta_config.json"
TASK_ID = "reflective_loop_001"


SEED_TRACE = """\
{"time":"2026-06-07T10:00:00+07:00","event_id":"evt_001","task_id":"reflective_loop_001","agent":"code_agent","framework":"generic","action":"edit_file","target":"src/ui.js","status":"completed","input":"Improve dashboard layout","output":"Updated layout structure","error":null,"metadata":{"files_changed":["src/ui.js"]}}
{"time":"2026-06-07T10:01:00+07:00","event_id":"evt_002","task_id":"reflective_loop_001","agent":"test_agent","framework":"generic","action":"run_tests","target":"python -m pytest","status":"failed","input":"Validate after UI edit","output":null,"error":"test_dashboard_rendering failed","metadata":{"failures":1}}
{"time":"2026-06-07T10:02:00+07:00","event_id":"evt_003","task_id":"reflective_loop_001","agent":"code_agent","framework":"generic","action":"edit_file","target":"src/renderer.py","status":"completed","input":"Continue improving UI without inspecting failure","output":"Changed renderer again","error":null,"metadata":{"files_changed":["src/renderer.py"]}}
"""


def _reset_runtime_files() -> tuple[Path, Path, Path]:
    trace_path = DEMO_DIR / "trace.jsonl"
    reflections_path = DEMO_DIR / "reflections.jsonl"
    trace_path.write_text(SEED_TRACE, encoding="utf-8")
    reflections_path.write_text("", encoding="utf-8")
    return trace_path, reflections_path, DEMO_DIR / "dashboard.html"


def main() -> None:
    config = load_config(str(CONFIG_PATH))
    trace_path, reflections_path, dashboard_path = _reset_runtime_files()

    print("Reflective Body Agent Loop demo")
    print("=" * 40)

    report_before = observe(
        trace_path,
        goal=config.goal,
        task_id=TASK_ID,
        reflections_path=reflections_path,
        record_reflection=True,
    )
    print("Step 1 - Citta reflects on problematic trace:")
    print(f"  decision: {report_before['decision']}")
    print(f"  next recommendation: {report_before['reflection']['next_recommendation']}")

    body_event = append_reflective_trace_event(
        trace_path,
        reflections_path,
        task_id=TASK_ID,
    )
    print()
    print("Step 2 - Reflective body agent acts:")
    print(f"  action: {body_event['action']}")
    print(f"  lesson_applied: {body_event['metadata']['lesson_applied']}")

    report_after = observe(
        trace_path,
        goal=config.goal,
        task_id=TASK_ID,
        reflections_path=reflections_path,
        record_reflection=True,
    )
    render_dashboard(
        report_after,
        dashboard_path,
        refresh_interval_seconds=config.refresh_interval_seconds,
    )

    print()
    print("Step 3 - Citta observes loop closure:")
    print(json.dumps(report_after["body_loop_status"], indent=2, ensure_ascii=False))
    print()
    print(f"Dashboard: {dashboard_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
