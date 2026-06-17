"""Render Citta reports as standalone dependency-free HTML."""

from __future__ import annotations

from html import escape
from pathlib import Path
from typing import Any

from .schemas import ActionStatus, to_dict
from .storage import write_text


def _value(value: Any) -> str:
    if value is None:
        return ""
    return escape(str(value))


def _risk_class(severity: str) -> str:
    return f"risk-{escape(severity or 'low')}"


def render_refresh_meta(refresh_interval_seconds: int = 0) -> str:
    if refresh_interval_seconds > 0:
        return f'  <meta http-equiv="refresh" content="{refresh_interval_seconds}">\n'
    return ""


def render_auto_refresh_status(refresh_interval_seconds: int = 0) -> str:
    if refresh_interval_seconds > 0:
        return f"Auto-refresh: every {refresh_interval_seconds} seconds"
    return "Auto-refresh: disabled"


def render_action_buttons(actions: list[dict[str, Any]], task_id: str | None = None) -> str:
    if not actions:
        return "<p>No recommended actions.</p>"

    forms: list[str] = []
    task_input = (
        f'  <input type="hidden" name="task_id" value="{escape(task_id)}">'
        if task_id
        else ""
    )
    for action in actions:
        name = str(action.get("action", ""))
        level = str(action.get("permission_level", "safe"))
        label = str(action.get("label") or name)
        reason = str(action.get("reason", ""))
        warning = ""
        if level in {"dangerous", "forbidden"}:
            warning = f'<span class="warning">Requires {escape(level)} handling</span>'
        forms.append(
            "\n".join(
                [
                    '<form method="post" action="/action" class="action-form">',
                    task_input,
                    f'  <input type="hidden" name="action" value="{escape(name)}">',
                    f'  <input type="hidden" name="reason" value="{escape(reason)}">',
                    f'  <input type="hidden" name="permission_level" value="{escape(level)}">',
                    f'  <button class="action action-{escape(level)}" type="submit">{escape(label)}</button>',
                    f"  {warning}",
                    "</form>",
                ]
            )
        )
    return "\n".join(forms)


def render_risk_panel(risks: list[dict[str, Any]]) -> str:
    if not risks:
        return '<p class="empty">No risks detected.</p>'
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
    return '<ul class="risks">' + "\n".join(items) + "</ul>"


def render_reflection_panel(reflection: dict[str, Any] | None) -> str:
    if not reflection:
        return '<p class="empty">No reflection recorded for this observation.</p>'
    fields = [
        ("Goal", reflection.get("goal")),
        ("Action", reflection.get("action")),
        ("Result", reflection.get("result")),
        ("Risk / Mistake", reflection.get("risk_or_mistake")),
        ("Lesson", reflection.get("lesson")),
        ("Next Recommendation", reflection.get("next_recommendation")),
    ]
    rows = []
    for label, value in fields:
        rows.append(
            "<tr>"
            f"<th>{escape(label)}</th>"
            f"<td>{_value(value)}</td>"
            "</tr>"
        )
    return (
        '<table class="reflection-table"><tbody>'
        + "\n".join(rows)
        + "</tbody></table>"
    )


def render_reflection_insights(insights: dict[str, Any]) -> str:
    if not insights or insights.get("total_reflections", 0) == 0:
        return '<p class="empty">No reflection insights yet.</p>'

    rows = [
        ("Total reflections", insights.get("total_reflections")),
        ("Most repeated lesson count", insights.get("most_repeated_lesson_count")),
        ("Most repeated mistake count", insights.get("most_repeated_mistake_count")),
        (
            "Repeated lesson ignored",
            "yes" if insights.get("repeated_lesson_ignored") else "no",
        ),
    ]
    body = []
    for label, value in rows:
        body.append(
            "<tr>"
            f"<th>{escape(label)}</th>"
            f"<td>{_value(value)}</td>"
            "</tr>"
        )

    lesson = insights.get("most_repeated_lesson")
    if lesson:
        body.append(
            "<tr>"
            f"<th>Most repeated lesson</th>"
            f"<td>{_value(lesson)}</td>"
            "</tr>"
        )

    return (
        '<table class="reflection-table"><tbody>'
        + "\n".join(body)
        + "</tbody></table>"
    )


def render_reflection_history(reflections: list[dict[str, Any]]) -> str:
    if not reflections:
        return '<p class="empty">No reflection history yet.</p>'
    rows = []
    for reflection in reflections[-10:]:
        rows.append(
            "<tr>"
            f"<td>{_value(reflection.get('time'))}</td>"
            f"<td>{_value(reflection.get('action'))}</td>"
            f"<td>{_value(reflection.get('lesson'))}</td>"
            f"<td>{_value(reflection.get('next_recommendation'))}</td>"
            "</tr>"
        )
    return (
        "<table><thead><tr><th>Time</th><th>Action</th><th>Lesson</th>"
        "<th>Next Recommendation</th></tr></thead><tbody>"
        + "\n".join(rows)
        + "</tbody></table>"
    )


def render_recent_trace(events: list[dict[str, Any]]) -> str:
    if not events:
        return '<p class="empty">No recent trace events.</p>'
    rows = []
    for event in events[-20:]:
        rows.append(
            "<tr>"
            f"<td>{_value(event.get('time'))}</td>"
            f"<td>{_value(event.get('agent'))}</td>"
            f"<td>{_value(event.get('action'))}</td>"
            f"<td>{_value(event.get('target'))}</td>"
            f"<td><span class=\"status\">{_value(event.get('status'))}</span></td>"
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
        return '<p class="empty">No actions recorded yet.</p>'
    rows = []
    for action in actions[-20:]:
        status = str(action.get("status") or "confirmed")
        action_id = str(action.get("action_id", ""))
        confirmation_links = ""
        if status == ActionStatus.PENDING_CONFIRMATION.value:
            confirmation_links = (
                f'<a class="link-button" href="/confirm?action_id={escape(action_id)}">Review</a>'
            )
        rows.append(
            "<tr>"
            f"<td>{_value(action.get('time'))}</td>"
            f"<td>{_value(action.get('action'))}</td>"
            f"<td>{_value(action.get('target') or action.get('task_id'))}</td>"
            f"<td>{_value(action.get('permission_level'))}</td>"
            f"<td><span class=\"status status-{escape(status)}\">{escape(status)}</span></td>"
            f"<td>{_value(action.get('reason'))}</td>"
            f"<td>{confirmation_links}</td>"
            "</tr>"
        )
    return (
        "<table><thead><tr><th>Time</th><th>Action</th><th>Target</th>"
        "<th>Permission</th><th>Confirmation status</th><th>Reason</th><th>Review</th>"
        "</tr></thead><tbody>"
        + "\n".join(rows)
        + "</tbody></table>"
    )


def _style() -> str:
    return """
  <style>
    :root { color-scheme: light dark; font-family: system-ui, sans-serif; }
    body { margin: 0; background: #10141c; color: #edf2f7; }
    header { padding: 2rem; background: linear-gradient(135deg, #172033, #1a365d); border-bottom: 1px solid #2d3748; }
    main { display: grid; gap: 1rem; padding: 1rem; max-width: 1180px; margin: 0 auto; }
    section, .card { background: #151b29; border: 1px solid #2d3748; border-radius: 14px; padding: 1rem; box-shadow: 0 8px 24px rgb(0 0 0 / 18%); }
    h1, h2 { margin-top: 0; }
    table { width: 100%; border-collapse: collapse; font-size: 0.92rem; }
    th, td { border-bottom: 1px solid #2d3748; padding: 0.55rem; text-align: left; vertical-align: top; }
    th { color: #bee3f8; }
    .reflection-table th { width: 12rem; vertical-align: top; }
    .badge { display: inline-block; padding: 0.2rem 0.55rem; border-radius: 999px; background: #2d3748; margin: 0.1rem; }
    .actions { display: flex; flex-wrap: wrap; gap: 0.75rem; }
    .action-form { display: inline-flex; align-items: center; gap: 0.5rem; }
    button, .link-button { border: 0; border-radius: 8px; padding: 0.7rem 1rem; cursor: pointer; font-weight: 700; text-decoration: none; display: inline-block; }
    .action-safe { background: #2f855a; color: white; }
    .action-medium { background: #b7791f; color: white; }
    .action-dangerous { background: #c53030; color: white; }
    .action-forbidden { background: #742a2a; color: white; }
    .link-button { background: #2b6cb0; color: white; }
    .risk-low { color: #90cdf4; }
    .risk-medium { color: #f6e05e; }
    .risk-high { color: #fc8181; }
    .risk-critical { color: #feb2b2; font-weight: 700; }
    .warning { color: #fbd38d; font-weight: 700; }
    .empty { color: #a0aec0; }
    .status { border-radius: 999px; background: #2d3748; padding: 0.1rem 0.45rem; white-space: nowrap; }
    .status-pending_confirmation { background: #975a16; color: white; }
    .status-confirmed { background: #276749; color: white; }
    .status-blocked { background: #9b2c2c; color: white; }
    code { background: #252f43; padding: 0.1rem 0.3rem; border-radius: 4px; }
  </style>
"""


def render_dashboard_html(
    report: dict[str, Any],
    *,
    refresh_interval_seconds: int = 0,
    page_title: str = "Citta Console",
) -> str:
    events = [to_dict(event) for event in report.get("events", [])]
    risks = [to_dict(risk) for risk in report.get("risks", [])]
    actions = [to_dict(action) for action in report.get("recommended_actions", [])]
    action_history = [to_dict(action) for action in report.get("action_history", [])]
    reflection = report.get("reflection")
    reflection_history = [to_dict(item) for item in report.get("reflection_history", [])]
    reflection_insights = report.get("reflection_insights") or {}
    agents = report.get("active_agents", [])
    goal = report.get("goal") or "No goal supplied"
    task_id = str(report.get("task_id", "default"))
    refresh_status = render_auto_refresh_status(refresh_interval_seconds)

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
{render_refresh_meta(refresh_interval_seconds)}  <title>{escape(page_title)}</title>
{_style()}</head>
<body>
  <header>
    <h1>{escape(page_title)}</h1>
    <p>A universal HTML control panel for agent awareness and action chaining.</p>
    <p><strong>Task:</strong> <a class="link-button" href="/task/{escape(task_id)}">{escape(task_id)}</a> &middot;
       <strong>Status:</strong> <code>{_value(report.get("current_state"))}</code></p>
    <p><strong>Goal:</strong> {_value(goal)}</p>
    <p><strong>{escape(refresh_status)}</strong></p>
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
      <p class="empty">Medium and dangerous actions create a pending confirmation record before they can be confirmed.</p>
      <div class="actions">{render_action_buttons(actions, task_id=task_id)}</div>
    </section>

    <section>
      <h2>Self-Reflection</h2>
      <p class="empty">Contextual post-action reflection recorded as JSONL evidence. Not a claim of consciousness.</p>
      {render_reflection_panel(reflection if isinstance(reflection, dict) else None)}
    </section>

    <section>
      <h2>Reflection Insights</h2>
      <p class="empty">Lesson-aware signals derived from reflection history. Not consciousness.</p>
      {render_reflection_insights(reflection_insights if isinstance(reflection_insights, dict) else {})}
    </section>

    <section>
      <h2>Reflection History</h2>
      {render_reflection_history(reflection_history)}
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


def render_task_detail_html(
    report: dict[str, Any],
    *,
    refresh_interval_seconds: int = 0,
) -> str:
    return render_dashboard_html(
        report,
        refresh_interval_seconds=refresh_interval_seconds,
        page_title="Citta Task Detail",
    )


def render_confirmation_page(action: dict[str, Any] | None) -> str:
    if not action:
        body = '<p class="empty">Action not found.</p><p><a class="link-button" href="/">Back</a></p>'
    else:
        action_id = str(action.get("action_id", ""))
        body = f"""
        <div class="card">
          <h2>Confirm Action</h2>
          <p><strong>Action:</strong> {_value(action.get("action"))}</p>
          <p><strong>Permission:</strong> {_value(action.get("permission_level"))}</p>
          <p><strong>Status:</strong> {_value(action.get("status"))}</p>
          <p><strong>Target:</strong> {_value(action.get("target"))}</p>
          <p><strong>Reason:</strong> {_value(action.get("reason"))}</p>
          <form method="post" action="/confirm">
            <input type="hidden" name="action_id" value="{escape(action_id)}">
            <button class="action action-medium" type="submit">Confirm</button>
          </form>
          <form method="post" action="/cancel">
            <input type="hidden" name="action_id" value="{escape(action_id)}">
            <button class="action action-dangerous" type="submit">Cancel</button>
          </form>
          <p><a class="link-button" href="/">Back to dashboard</a></p>
        </div>
        """
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Citta Action Confirmation</title>
{_style()}</head>
<body>
  <header><h1>Citta Action Confirmation</h1></header>
  <main>{body}</main>
</body>
</html>
"""


def render_dashboard(
    report: dict[str, Any],
    output_path: str | Path,
    *,
    refresh_interval_seconds: int = 0,
) -> Path:
    return write_text(
        output_path,
        render_dashboard_html(report, refresh_interval_seconds=refresh_interval_seconds),
    )
