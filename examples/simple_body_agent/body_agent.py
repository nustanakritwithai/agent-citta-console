"""A tiny body agent that reacts to Citta actions.jsonl.

It demonstrates the MVP loop:
body agent writes trace -> Citta renders HTML -> user dispatches action ->
body agent reads action -> body agent writes another trace event.
"""

from __future__ import annotations

import json
from pathlib import Path

from citta_console.schemas import make_id, now_iso
from citta_console.storage import read_jsonl


ROOT = Path(__file__).resolve().parents[2]
TRACE_PATH = ROOT / "examples" / "generic_jsonl" / "trace.jsonl"
ACTIONS_PATH = ROOT / "examples" / "generic_jsonl" / "actions.jsonl"


def append_event(action_name: str, status: str, output: str) -> None:
    event = {
        "time": now_iso(),
        "event_id": make_id("evt"),
        "task_id": "task_001",
        "agent": "simple_body_agent",
        "framework": "generic",
        "action": action_name,
        "target": "actions.jsonl",
        "status": status,
        "input": "Read dispatched action",
        "output": output,
        "error": None,
        "metadata": {"source": "examples/simple_body_agent/body_agent.py"},
    }
    with TRACE_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")


def main() -> None:
    actions = read_jsonl(ACTIONS_PATH)
    if not actions:
        append_event("wait_for_action", "blocked", "No dispatched actions yet.")
        print("No actions found; wrote blocked trace event.")
        return
    latest = actions[-1]
    action_name = str(latest.get("action", "continue"))
    append_event(action_name, "completed", f"Handled action {action_name}.")
    print(f"Handled action {action_name}.")


if __name__ == "__main__":
    main()
