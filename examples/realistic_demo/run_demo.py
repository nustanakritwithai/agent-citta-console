"""Generate the realistic Citta demo dashboard."""

from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from citta_console.config import load_config
from citta_console.observer import observe
from citta_console.renderer import render_dashboard

CONFIG_PATH = ROOT / "examples" / "realistic_demo" / "citta_config.json"


def main() -> None:
    config = load_config(str(CONFIG_PATH))
    report = observe(
        ROOT / config.trace_path,
        actions_path=ROOT / config.actions_path,
        goal=config.goal,
        task_id="ui_refactor_001",
    )
    output_path = render_dashboard(
        report,
        ROOT / config.dashboard_path,
        refresh_interval_seconds=config.refresh_interval_seconds,
    )
    relative_output = output_path.relative_to(ROOT)
    print("Generated realistic Citta dashboard:")
    print(relative_output)
    print()
    print("Open this file in your browser to see:")
    print("- current state")
    print("- detected risks")
    print("- recommended actions")
    print("- action history")
    print()
    print(f"Decision: {report['decision']} - {report['reason']}")


if __name__ == "__main__":
    main()
