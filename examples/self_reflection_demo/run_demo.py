"""Demonstrate the Self-Reflection Trace MVP loop.

Body agent leaves trace events.
Citta observes, reflects, records reflection JSONL, and renders a dashboard.
"""

from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from citta_console.config import load_config
from citta_console.observer import observe
from citta_console.renderer import render_dashboard

CONFIG_PATH = ROOT / "examples" / "self_reflection_demo" / "citta_config.json"


def main() -> None:
    config = load_config(str(CONFIG_PATH))
    reflections_path = ROOT / "examples" / "self_reflection_demo" / "reflections.jsonl"
    report = observe(
        ROOT / config.trace_path,
        actions_path=ROOT / config.actions_path,
        reflections_path=reflections_path,
        record_reflection=True,
        goal=config.goal,
        task_id="self_reflection_001",
    )
    output_path = render_dashboard(
        report,
        ROOT / config.dashboard_path,
        refresh_interval_seconds=config.refresh_interval_seconds,
    )

    print("Self-Reflection Trace MVP demo")
    print("=" * 40)
    print(f"Dashboard: {output_path.relative_to(ROOT)}")
    print(f"Reflections: {reflections_path.relative_to(ROOT)}")
    print()
    print("Latest reflection:")
    print(json.dumps(report["reflection"], indent=2, ensure_ascii=False))
    print()
    print(f"Decision: {report['decision']} - {report['reason']}")


if __name__ == "__main__":
    main()
