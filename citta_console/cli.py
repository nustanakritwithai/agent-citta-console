"""Command-line interface for local Citta tool calls."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from .tools.dispatcher import dispatch_tool


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="citta-console")
    subparsers = parser.add_subparsers(dest="command", required=True)

    tool_parser = subparsers.add_parser("tool", help="Call a local Citta tool")
    tool_parser.add_argument("tool_name")
    tool_parser.add_argument("--json", default="{}", help="JSON object input")

    args = parser.parse_args(argv)
    if args.command == "tool":
        return _run_tool(args.tool_name, args.json)
    parser.error(f"unknown command: {args.command}")
    return 2


def _run_tool(tool_name: str, json_input: str) -> int:
    try:
        payload = json.loads(json_input)
    except json.JSONDecodeError as exc:
        _print_json({"ok": False, "error": f"invalid JSON input: {exc}"})
        return 2
    if not isinstance(payload, dict):
        _print_json({"ok": False, "error": "tool input must be a JSON object"})
        return 2

    result = dispatch_tool(tool_name, payload)
    _print_json(result)
    return 0 if result.get("ok") else 1


def _print_json(value: dict[str, Any]) -> None:
    print(json.dumps(value, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    raise SystemExit(main())
