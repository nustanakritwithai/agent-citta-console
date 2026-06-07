"""Append one sample event to the generic trace."""

from __future__ import annotations

import json
from pathlib import Path

from citta_console.schemas import make_id, now_iso


ROOT = Path(__file__).resolve().parents[2]
TRACE_PATH = ROOT / "examples" / "generic_jsonl" / "trace.jsonl"


def main() -> None:
    event = {
        "time": now_iso(),
        "event_id": make_id("evt"),
        "task_id": "task_001",
        "agent": "demo_writer",
        "framework": "generic",
        "action": "summarize_state",
        "target": "trace.jsonl",
        "status": "completed",
        "output": "Demo trace writer added an event.",
        "error": None,
        "metadata": {"confidence": 0.9},
    }
    with TRACE_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")
    print(f"Appended event to {TRACE_PATH}")


if __name__ == "__main__":
    main()
