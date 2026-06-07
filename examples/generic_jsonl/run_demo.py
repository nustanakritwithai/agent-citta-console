"""Generate a Citta HTML dashboard from the generic JSONL example."""

from __future__ import annotations

from pathlib import Path

from citta_console.observer import observe
from citta_console.renderer import render_dashboard


ROOT = Path(__file__).resolve().parents[2]
TRACE_PATH = ROOT / "examples" / "generic_jsonl" / "trace.jsonl"
ACTIONS_PATH = ROOT / "examples" / "generic_jsonl" / "actions.jsonl"
DASHBOARD_PATH = ROOT / "examples" / "html_console_demo" / "dashboard.html"


def main() -> None:
    report = observe(
        TRACE_PATH,
        actions_path=ACTIONS_PATH,
        goal="Build an MVP universal HTML control panel for agent traces.",
    )
    output_path = render_dashboard(report, DASHBOARD_PATH)
    print(f"Wrote {output_path}")
    print(f"Decision: {report['decision']} - {report['reason']}")


if __name__ == "__main__":
    main()
