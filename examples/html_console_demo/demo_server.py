"""Run the standard-library Citta Console demo server."""

from __future__ import annotations

from pathlib import Path

from citta_console.server import run_server


ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    run_server(
        trace_path=ROOT / "examples" / "generic_jsonl" / "trace.jsonl",
        actions_path=ROOT / "examples" / "generic_jsonl" / "actions.jsonl",
        goal="Observe generic JSONL traces and dispatch safe next actions.",
    )


if __name__ == "__main__":
    main()
