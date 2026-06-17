"""Run the reflective body agent loop demo via the automatic loop runner."""

from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from citta_console.config import load_config
from citta_console.reflective_loop import run_reflective_loop

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

    result = run_reflective_loop(
        trace_path,
        task_id=TASK_ID,
        goal=config.goal,
        reflections_path=reflections_path,
        dashboard_path=dashboard_path,
        max_iterations=3,
        refresh_interval_seconds=config.refresh_interval_seconds,
    )

    print("Reflective Body Agent Loop demo (auto-loop)")
    print("=" * 40)
    print(f"stop_reason: {result['stop_reason']}")
    print(f"iterations: {result['iterations']}")
    print()
    print("steps:")
    print(json.dumps(result["steps"], indent=2, ensure_ascii=False))
    print()
    print("final body_loop_status:")
    print(json.dumps(result["final_report"]["body_loop_status"], indent=2, ensure_ascii=False))
    print()
    print(f"Dashboard: {dashboard_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
