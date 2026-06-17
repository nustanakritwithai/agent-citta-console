"""Command-line interface for local Citta tool calls."""

from __future__ import annotations

import argparse
import json
import signal
import sys
from typing import Any

from .agent_runtime import (
    DEFAULT_TASK_ID,
    get_runtime_status,
    record_agent_event,
    record_user_request,
)
from .config import load_config
from .reflective_daemon import run_reflective_daemon
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

    loop_daemon = loop_subparsers.add_parser(
        "daemon",
        help="Continuously poll trace changes and run reflective ticks",
    )
    loop_daemon.add_argument("--config", help="Optional Citta config JSON path")
    loop_daemon.add_argument("--trace", help="Trace JSONL path")
    loop_daemon.add_argument("--reflections", help="Reflections JSONL path")
    loop_daemon.add_argument("--actions", help="Actions JSONL path")
    loop_daemon.add_argument("--dashboard", help="Dashboard HTML output path")
    loop_daemon.add_argument("--task-id", required=True, help="Task id to watch")
    loop_daemon.add_argument("--goal", help="Optional task goal")
    loop_daemon.add_argument("--poll-interval", type=float, default=2.0)
    loop_daemon.add_argument(
        "--max-cycles",
        type=int,
        help="Optional safety limit; default runs until interrupted",
    )
    loop_daemon.add_argument(
        "--fallback-action",
        default="edit_file",
        help="Body action when no reflection exists yet",
    )
    loop_daemon.add_argument(
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

    runtime_parser = subparsers.add_parser(
        "runtime",
        help="Operate the always-on agent Citta runtime",
    )
    runtime_subparsers = runtime_parser.add_subparsers(dest="runtime_command", required=True)
    runtime_status = runtime_subparsers.add_parser(
        "status",
        help="Observe the agent runtime and render its dashboard",
    )
    runtime_status.add_argument("--task-id", default=DEFAULT_TASK_ID)
    runtime_status.add_argument("--config", help="Optional runtime config JSON path")
    runtime_status.add_argument(
        "--record-reflection",
        action="store_true",
        help="Append a reflection record while observing",
    )
    runtime_record = runtime_subparsers.add_parser(
        "record",
        help="Append one agent event to the runtime trace",
    )
    runtime_record.add_argument("--action", required=True)
    runtime_record.add_argument("--target")
    runtime_record.add_argument("--status", default="completed")
    runtime_record.add_argument("--input")
    runtime_record.add_argument("--output")
    runtime_record.add_argument("--error")
    runtime_record.add_argument("--task-id", default=DEFAULT_TASK_ID)
    runtime_record.add_argument("--config", help="Optional runtime config JSON path")
    runtime_record.add_argument(
        "--metadata",
        default="{}",
        help="Optional JSON metadata object",
    )
    runtime_user = runtime_subparsers.add_parser(
        "user",
        help="Record a user request in the runtime trace",
    )
    runtime_user.add_argument("content")
    runtime_user.add_argument("--task-id", default=DEFAULT_TASK_ID)
    runtime_user.add_argument("--config", help="Optional runtime config JSON path")

    args = parser.parse_args(argv)
    if args.command == "tool":
        return _run_tool(args.tool_name, args.json)
    if args.command == "loop" and args.loop_command == "run":
        return _run_loop(args)
    if args.command == "loop" and args.loop_command == "daemon":
        return _run_daemon(args)
    if args.command == "hermes" and args.hermes_command == "observe":
        return _run_hermes_observe(args)
    if args.command == "runtime" and args.runtime_command == "status":
        return _run_runtime_status(args)
    if args.command == "runtime" and args.runtime_command == "record":
        return _run_runtime_record(args)
    if args.command == "runtime" and args.runtime_command == "user":
        return _run_runtime_user(args)
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


def _loop_paths(args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    try:
        config = load_config(args.config) if args.config else None
    except (FileNotFoundError, ValueError) as exc:
        _print_json({"ok": False, "error": str(exc)})
        return {}, 2

    trace_path = args.trace or (config.trace_path if config else None)
    if not trace_path:
        _print_json({"ok": False, "error": "trace path is required via --trace or --config"})
        return {}, 2

    return {
        "trace_path": trace_path,
        "reflections_path": args.reflections or str(default_reflections_path(trace_path)),
        "actions_path": args.actions or (config.actions_path if config else None),
        "dashboard_path": args.dashboard or (config.dashboard_path if config else None),
        "goal": args.goal if args.goal is not None else (config.goal if config else None),
        "refresh_interval_seconds": config.refresh_interval_seconds if config else 0,
        "task_id": args.task_id,
        "record_reflection": not args.no_record_reflection,
        "fallback_action": args.fallback_action,
    }, 0


def _run_loop(args: argparse.Namespace) -> int:
    paths, exit_code = _loop_paths(args)
    if exit_code != 0:
        return exit_code

    try:
        result = run_reflective_loop(
            paths["trace_path"],
            task_id=paths["task_id"],
            goal=paths["goal"],
            actions_path=paths["actions_path"],
            reflections_path=paths["reflections_path"],
            dashboard_path=paths["dashboard_path"],
            max_iterations=args.max_iterations,
            record_reflection=paths["record_reflection"],
            fallback_action=paths["fallback_action"],
            refresh_interval_seconds=paths["refresh_interval_seconds"],
        )
    except ValueError as exc:
        _print_json({"ok": False, "error": str(exc)})
        return 2

    _print_json(result)
    return 0


def _run_daemon(args: argparse.Namespace) -> int:
    paths, exit_code = _loop_paths(args)
    if exit_code != 0:
        return exit_code

    stop_requested = False

    def _handle_signal(_signum: int, _frame: object) -> None:
        nonlocal stop_requested
        stop_requested = True

    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    try:
        result = run_reflective_daemon(
            paths["trace_path"],
            task_id=paths["task_id"],
            goal=paths["goal"],
            actions_path=paths["actions_path"],
            reflections_path=paths["reflections_path"],
            dashboard_path=paths["dashboard_path"],
            poll_interval_seconds=args.poll_interval,
            record_reflection=paths["record_reflection"],
            fallback_action=paths["fallback_action"],
            refresh_interval_seconds=paths["refresh_interval_seconds"],
            max_cycles=args.max_cycles,
            should_stop=lambda: stop_requested,
        )
    except ValueError as exc:
        _print_json({"ok": False, "error": str(exc)})
        return 2

    _print_json(result)
    return 0


def _print_json(value: dict[str, Any]) -> None:
    print(json.dumps(value, ensure_ascii=False, sort_keys=True))


def _run_runtime_status(args: argparse.Namespace) -> int:
    result = get_runtime_status(
        task_id=args.task_id,
        config_path=args.config,
        record_reflection=args.record_reflection,
    )
    _print_json(result)
    return 0


def _run_runtime_record(args: argparse.Namespace) -> int:
    try:
        metadata = json.loads(args.metadata)
    except json.JSONDecodeError as exc:
        _print_json({"ok": False, "error": f"invalid metadata JSON: {exc}"})
        return 2
    if not isinstance(metadata, dict):
        _print_json({"ok": False, "error": "metadata must be a JSON object"})
        return 2

    event = record_agent_event(
        action=args.action,
        target=args.target,
        status=args.status,
        input=args.input,
        output=args.output,
        error=args.error,
        metadata=metadata,
        task_id=args.task_id,
        config_path=args.config,
    )
    _print_json({"ok": True, "event": event})
    return 0


def _run_runtime_user(args: argparse.Namespace) -> int:
    event = record_user_request(
        args.content,
        task_id=args.task_id,
        config_path=args.config,
    )
    _print_json({"ok": True, "event": event})
    return 0


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
