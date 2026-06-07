"""Command-line interface for local Citta tool calls."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from .skills.hermes_citta_skill.run_observer import (
    add_observe_arguments,
    print_observer_result,
    run_observer,
)
from .tools.dispatcher import dispatch_tool


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="citta-console")
    subparsers = parser.add_subparsers(dest="command", required=True)

    tool_parser = subparsers.add_parser("tool", help="Call a local Citta tool")
    tool_parser.add_argument("tool_name")
    tool_parser.add_argument("--json", default="{}", help="JSON object input")

    hermes_parser = subparsers.add_parser("hermes", help="Hermes Citta Skill commands")
    hermes_subparsers = hermes_parser.add_subparsers(dest="hermes_command", required=True)
    hermes_observe = hermes_subparsers.add_parser(
        "observe",
        help="Run the experimental Hermes Citta Skill observer",
    )
    add_observe_arguments(hermes_observe)

    args = parser.parse_args(argv)
    if args.command == "tool":
        return _run_tool(args.tool_name, args.json)
    if args.command == "hermes" and args.hermes_command == "observe":
        return _run_hermes_observe(args)
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


def _run_hermes_observe(args: argparse.Namespace) -> int:
    try:
        _report, risks, actions = run_observer(
            trace=args.trace,
            actions=args.actions,
            dashboard=args.dashboard,
            goal=args.goal,
            task_id=args.task_id,
        )
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    print_observer_result(args.dashboard, risks, actions)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
