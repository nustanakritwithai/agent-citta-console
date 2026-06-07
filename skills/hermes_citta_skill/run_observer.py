"""Run Citta observer for the experimental Hermes skill."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from skills.hermes_citta_skill.citta_skill import HermesCittaSkill


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run Hermes Citta Skill observer")
    parser.add_argument("--trace", required=True)
    parser.add_argument("--actions", required=True)
    parser.add_argument("--dashboard", required=True)
    parser.add_argument("--goal", default=None)
    parser.add_argument("--task-id", default=None)
    args = parser.parse_args(argv)

    skill = HermesCittaSkill(args.trace, args.actions, args.dashboard)
    report = skill.observe(goal=args.goal, task_id=args.task_id)
    risks = [risk["type"] for risk in report.get("risks", [])]
    actions = [action["action"] for action in report.get("recommended_actions", [])]

    print(f"Dashboard: {args.dashboard}")
    print("Detected risks:")
    for risk in risks:
        print(f"- {risk}")
    print("Recommended actions:")
    for action in actions:
        print(f"- {action}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
