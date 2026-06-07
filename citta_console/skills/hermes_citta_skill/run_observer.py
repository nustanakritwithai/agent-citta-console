"""Run Citta observer for the experimental Hermes skill."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from citta_console.skills.hermes_citta_skill.citta_skill import HermesCittaSkill


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run Hermes Citta Skill observer")
    add_observe_arguments(parser)
    args = parser.parse_args(argv)

    report, risks, actions = run_observer(
        trace=args.trace,
        actions=args.actions,
        dashboard=args.dashboard,
        goal=args.goal,
        task_id=args.task_id,
    )
    print_observer_result(args.dashboard, risks, actions)
    return 0


def add_observe_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--trace", required=True)
    parser.add_argument("--actions", required=True)
    parser.add_argument("--dashboard", required=True)
    parser.add_argument("--goal", default=None)
    parser.add_argument("--task-id", default=None)


def run_observer(
    *,
    trace: str,
    actions: str,
    dashboard: str,
    goal: str | None = None,
    task_id: str | None = None,
) -> tuple[dict, list[str], list[str]]:
    skill = HermesCittaSkill(trace, actions, dashboard)
    report = skill.observe(goal=goal, task_id=task_id)
    risks = [risk["type"] for risk in report.get("risks", [])]
    actions = [action["action"] for action in report.get("recommended_actions", [])]
    return report, risks, actions


def print_observer_result(dashboard: str, risks: list[str], actions: list[str]) -> None:
    print(f"Dashboard: {dashboard}")
    print("Detected risks:")
    for risk in risks:
        print(f"- {risk}")
    print("Recommended actions:")
    for action in actions:
        print(f"- {action}")


if __name__ == "__main__":
    raise SystemExit(main())
