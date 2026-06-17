"""Command-line interface for local Citta tool calls."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from .config import load_config
from .reflective_loop import default_reflections_path, run_reflective_loop
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

    loop_parser = subparsers.add_parser(
        "loop",
        help="Run automatic reflective body loops",
    )
    loop_subparsers = loop_parser.add_subparsers(dest="loop_command", required=True)
    loop_run = loop_subparsers.add_parser(
        "run",
        help="Observe, reflect, and let the reflective body agent act in a loop",
    )
    loop_run.add_argument("--config", help="Optional Citta config JSON path")
    loop_run.add_argument("--trace", help="Trace JSONL path")
    loop_run.add_argument("--reflections", help="Reflections JSONL path")
    loop_run.add_argument("--actions", help="Actions JSONL path")
    loop_run.add_argument("--dashboard", help="Dashboard HTML output path")
    loop_run.add_argument("--task-id", required=True, help="Task id to run")
    loop_run.add_argument("--goal", help="Optional task goal")
    loop_run.add_argument("--max-iterations", type=int, default=5)
    loop_run.add_argument(
        "--fallback-action",
        default="edit_file",
        help="Body action when no reflection exists yet",
    )
    loop_run.add_argument(
        "--no-record-reflection",
        action="store_true",
        help="Observe without appending new reflection records",
    )

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
    if args.command == "loop" and args.loop_command == "run":
        return _run_loop(args)
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


def _run_loop(args: argparse.Namespace) -> int:
    try:
        config = load_config(args.config) if args.config else None
    except (FileNotFoundError, ValueError) as exc:
        _print_json({"ok": False, "error": str(exc)})
        return 2

    trace_path = args.trace or (config.trace_path if config else None)
    if not trace_path:
        _print_json({"ok": False, "error": "trace path is required via --trace or --config"})
        return 2

    reflections_path = args.reflections or str(default_reflections_path(trace_path))
    actions_path = args.actions or (config.actions_path if config else None)
    dashboard_path = args.dashboard or (config.dashboard_path if config else None)
    goal = args.goal if args.goal is not None else (config.goal if config else None)
    refresh_interval_seconds = config.refresh_interval_seconds if config else 0

    try:
        result = run_reflective_loop(
            trace_path,
            task_id=args.task_id,
            goal=goal,
            actions_path=actions_path,
            reflections_path=reflections_path,
            dashboard_path=dashboard_path,
            max_iterations=args.max_iterations,
            record_reflection=not args.no_record_reflection,
            fallback_action=args.fallback_action,
            refresh_interval_seconds=refresh_interval_seconds,
        )
    except ValueError as exc:
        _print_json({"ok": False, "error": str(exc)})
        return 2

    _print_json(result)
    return 0


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
