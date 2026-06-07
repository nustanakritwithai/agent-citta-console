"""Render Citta reports as standalone HTML dashboards."""

from __future__ import annotations

from html import escape
from pathlib import Path
from typing import Any

from .schemas import to_dict
from .storage import write_text


def _value(value: Any) -> str:
    if value is None:
        return ""
    return escape(str(value))


def _risk_class(severity: str) -> str:
    return f"risk-{escape(severity or 'low')}"


def render_action_buttons(actions: list[dict[str, Any]]) -> str:
    if not actions:
        return "<p>No recommended actions.</p>"

    forms: list[str] = []
    for action in actions:
        name = str(action.get("action", ""))
        level = str(action.get("permission_level", "safe"))
        label = str(action.get("label") or name)
        reason = str(action.get("reason", ""))
        confirm = ""
        if level in {"medium", "dangerous"}:
            confirm = (
                " data-confirm=\"true\""
                f" onsubmit=\"return confirm('{escape(label)} requires {escape(level)} permission. Continue?')\""
            )
        forms.append(
            "\n".join(
                [
                    f'<form method="post" action="/action"{confirm}>',
                    f'  <input type="hidden" name="action" value="{escape(name)}">',
                    f'  <input type="hidden" name="reason" value="{escape(reason)}">',
                    f'  <input type="hidden" name="permission_level" value="{escape(level)}">',
                    f'  <button class="action action-{escape(level)}" type="submit">{escape(label)}</button>',
                    "</form>",
                ]
            )
        )
    return "\n".join(forms)


def render_risk_panel(risks: list[dict[str, Any]]) -> str:
    if not risks:
        return "<p class=\"empty\">No risks detected.</p>"
    items = []
    for risk in risks:
        severity = str(risk.get("severity", "low"))
        items.append(
            "<li class=\"{klass}\"><strong>{severity}:</strong> {rtype} - {reason}</li>".format(
                klass=_risk_class(severity),
                severity=escape(severity.title()),
                rtype=escape(str(risk.get("type", "risk"))),
                reason=escape(str(risk.get("reason", ""))),
            )
        )
    return "<ul class=\"risks\">" + "\n".join(items) + "</ul>"


def render_recent_trace(events: list[dict[str, Any]]) -> str:
    if not events:
        return "<p class=\"empty\">No recent trace events.</p>"
    rows = []
    for event in events[-20:]:
        rows.append(
            "<tr>"
            f"<td>{_value(event.get('time'))}</td>"
            f"<td>{_value(event.get('agent'))}</td>"
            f"<td>{_value(event.get('action'))}</td>"
            f"<td>{_value(event.get('target'))}</td>"
            f"<td>{_value(event.get('status'))}</td>"
            f"<td>{_value(event.get('error'))}</td>"
            "</tr>"
        )
    return (
        "<table><thead><tr><th>Time</th><th>Agent</th><th>Action</th>"
        "<th>Target</th><th>Status</th><th>Error</th></tr></thead><tbody>"
        + "\n".join(rows)
        + "</tbody></table>"
    )


def render_action_history(actions: list[dict[str, Any]]) -> str:
    if not actions:
        return "<p class=\"empty\">No actions have been dispatched yet.</p>"
    items = []
    for action in actions[-20:]:
        items.append(
            "<li><strong>{action}</strong> on {target} - {reason} <span>{time}</span></li>".format(
                action=_value(action.get("action")),
                target=_value(action.get("target") or action.get("task_id")),
                reason=_value(action.get("reason")),
                time=_value(action.get("time")),
            )
        )
    return "<ul class=\"history\">" + "\n".join(items) + "</ul>"


def render_dashboard_html(report: dict[str, Any]) -> str:
    events = [to_dict(event) for event in report.get("events", [])]
    risks = [to_dict(risk) for risk in report.get("risks", [])]
    actions = [to_dict(action) for action in report.get("recommended_actions", [])]
    action_history = [to_dict(action) for action in report.get("action_history", [])]
    agents = report.get("active_agents", [])
    goal = report.get("goal") or "No goal supplied"

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Citta Console</title>
  <style>
    :root {{ color-scheme: light dark; font-family: system-ui, sans-serif; }}
    body {{ margin: 0; background: #10141c; color: #edf2f7; }}
    header {{ padding: 2rem; background: #172033; border-bottom: 1px solid #2d3748; }}
    main {{ display: grid; gap: 1rem; padding: 1rem; max-width: 1100px; margin: 0 auto; }}
    section {{ background: #151b29; border: 1px solid #2d3748; border-radius: 12px; padding: 1rem; }}
    h1, h2 {{ margin-top: 0; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 0.92rem; }}
    th, td {{ border-bottom: 1px solid #2d3748; padding: 0.5rem; text-align: left; vertical-align: top; }}
    .badge {{ display: inline-block; padding: 0.2rem 0.5rem; border-radius: 999px; background: #2d3748; margin: 0.1rem; }}
    .actions {{ display: flex; flex-wrap: wrap; gap: 0.75rem; }}
    form {{ display: inline; }}
    button {{ border: 0; border-radius: 8px; padding: 0.7rem 1rem; cursor: pointer; font-weight: 700; }}
    .action-safe {{ background: #2f855a; color: white; }}
    .action-medium {{ background: #b7791f; color: white; }}
    .action-dangerous {{ background: #c53030; color: white; }}
    .risk-low {{ color: #90cdf4; }}
    .risk-medium {{ color: #f6e05e; }}
    .risk-high {{ color: #fc8181; }}
    .risk-critical {{ color: #feb2b2; font-weight: 700; }}
    .empty {{ color: #a0aec0; }}
    code {{ background: #252f43; padding: 0.1rem 0.3rem; border-radius: 4px; }}
  </style>
</head>
<body>
  <header>
    <h1>Citta Console</h1>
    <p>A universal HTML control panel for agent awareness and action chaining.</p>
    <p><strong>Task:</strong> {_value(report.get("task_id", "default"))} &middot;
       <strong>Status:</strong> <code>{_value(report.get("current_state"))}</code></p>
    <p><strong>Goal:</strong> {_value(goal)}</p>
  </header>
  <main>
    <section>
      <h2>Current State</h2>
      <p>{_value(report.get("summary") or report.get("reason"))}</p>
      <p><strong>Decision:</strong> {_value(report.get("decision"))} - {_value(report.get("reason"))}</p>
    </section>

    <section>
      <h2>Active Agents</h2>
      {''.join(f'<span class="badge">{escape(str(agent))}</span>' for agent in agents) or '<p class="empty">No active agents.</p>'}
    </section>

    <section>
      <h2>Risks</h2>
      {render_risk_panel(risks)}
    </section>

    <section>
      <h2>Recommended Actions</h2>
      <p class="empty">Medium and dangerous actions ask for confirmation before dispatch.</p>
      <div class="actions">{render_action_buttons(actions)}</div>
    </section>

    <section>
      <h2>Recent Trace</h2>
      {render_recent_trace(events)}
    </section>

    <section>
      <h2>Action History</h2>
      {render_action_history(action_history)}
    </section>
  </main>
</body>
</html>
"""


def render_dashboard(report: dict[str, Any], output_path: str | Path) -> Path:
    return write_text(output_path, render_dashboard_html(report))
