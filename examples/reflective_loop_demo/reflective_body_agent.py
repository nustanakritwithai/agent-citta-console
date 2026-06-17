"""Reflective body agent that applies the latest Citta reflection."""

from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from citta_console.body_policy import append_reflective_trace_event

DEMO_DIR = Path(__file__).resolve().parent
TRACE_PATH = DEMO_DIR / "trace.jsonl"
REFLECTIONS_PATH = DEMO_DIR / "reflections.jsonl"
TASK_ID = "reflective_loop_001"


def main() -> None:
    event = append_reflective_trace_event(
        TRACE_PATH,
        REFLECTIONS_PATH,
        task_id=TASK_ID,
    )
    metadata = event.get("metadata") or {}
    print(f"Reflective body agent wrote action: {event['action']}")
    print(f"Lesson applied: {metadata.get('lesson_applied')}")
    print(f"Source reflection: {metadata.get('source_reflection_id')}")


if __name__ == "__main__":
    main()
