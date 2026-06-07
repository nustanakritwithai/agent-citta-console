"""Local standard-library HTTP server for the Citta Console."""

from __future__ import annotations

import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from .config import CittaConfig, default_config, load_config
from .dispatcher import cancel_action, confirm_action, dispatch_action, find_action, read_actions
from .observer import observe
from .renderer import render_confirmation_page, render_dashboard_html, render_task_detail_html
from .trace_reader import events_to_dicts, read_trace


def parse_form_body(body: str) -> dict[str, str]:
    return {key: values[0] for key, values in parse_qs(body).items()}


def build_report(config: CittaConfig, task_id: str | None = None) -> dict[str, object]:
    return observe(
        config.trace_path,
        task_id=task_id,
        actions_path=config.actions_path,
        goal=config.goal,
    )


def latest_task_id(config: CittaConfig) -> str:
    events = read_trace(config.trace_path)
    if not events:
        return "default"
    return events[-1].task_id


def handle_action_submission(form: dict[str, str], config: CittaConfig) -> dict[str, object]:
    task_id = form.get("task_id") or latest_task_id(config)
    confirm = form.get("confirm") in {"1", "true", "yes", "on"}
    return dispatch_action(
        form,
        config.actions_path,
        task_id=task_id,
        confirm=confirm,
        require_confirmation_for_medium=config.require_confirmation_for_medium,
        require_confirmation_for_dangerous=config.require_confirmation_for_dangerous,
        block_forbidden_actions=config.block_forbidden_actions,
    )


def handle_confirm_submission(form: dict[str, str], config: CittaConfig) -> dict[str, object]:
    action_id = form.get("action_id", "")
    return confirm_action(config.actions_path, action_id)


def handle_cancel_submission(form: dict[str, str], config: CittaConfig) -> dict[str, object]:
    action_id = form.get("action_id", "")
    return cancel_action(config.actions_path, action_id)


class CittaRequestHandler(BaseHTTPRequestHandler):
    config = default_config()

    def _send(self, body: str, status: int = 200, content_type: str = "text/html") -> None:
        encoded = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", f"{content_type}; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def _read_form(self) -> dict[str, str]:
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length).decode("utf-8")
        return parse_form_body(body)

    def do_GET(self) -> None:  # noqa: N802 - http.server API
        parsed = urlparse(self.path)
        if parsed.path == "/":
            report = build_report(self.config)
            self._send(
                render_dashboard_html(
                    report,
                    refresh_interval_seconds=self.config.refresh_interval_seconds,
                )
            )
            return
        if parsed.path.startswith("/task/"):
            task_id = parsed.path.removeprefix("/task/")
            report = build_report(self.config, task_id=task_id)
            self._send(
                render_task_detail_html(
                    report,
                    refresh_interval_seconds=self.config.refresh_interval_seconds,
                )
            )
            return
        if parsed.path == "/actions":
            actions = read_actions(self.config.actions_path, limit=100)
            self._send(json.dumps(actions, indent=2), content_type="application/json")
            return
        if parsed.path == "/trace":
            self._send(
                json.dumps(events_to_dicts(read_trace(self.config.trace_path)), indent=2),
                content_type="application/json",
            )
            return
        if parsed.path == "/confirm":
            action_id = parse_qs(parsed.query).get("action_id", [""])[0]
            self._send(render_confirmation_page(find_action(self.config.actions_path, action_id)))
            return
        self._send("Not found", status=HTTPStatus.NOT_FOUND, content_type="text/plain")

    def do_POST(self) -> None:  # noqa: N802 - http.server API
        parsed = urlparse(self.path)
        form = self._read_form()
        try:
            if parsed.path == "/action":
                record = handle_action_submission(form, self.config)
            elif parsed.path == "/confirm":
                record = handle_confirm_submission(form, self.config)
            elif parsed.path == "/cancel":
                record = handle_cancel_submission(form, self.config)
            else:
                self._send("Not found", status=HTTPStatus.NOT_FOUND, content_type="text/plain")
                return
        except (PermissionError, ValueError) as exc:
            self._send(f"Action rejected: {exc}", status=HTTPStatus.BAD_REQUEST, content_type="text/plain")
            return

        self._send(
            "<html><body><h1>Action recorded</h1>"
            f"<pre>{json.dumps(record, indent=2)}</pre>"
            '<p><a href="/">Back to dashboard</a></p></body></html>'
        )


def run_server(
    host: str = "127.0.0.1",
    port: int = 8000,
    *,
    trace_path: str | Path | None = None,
    actions_path: str | Path | None = None,
    goal: str | None = None,
    config_path: str | None = None,
    config: CittaConfig | None = None,
) -> None:
    active_config = config or load_config(config_path)
    if trace_path is not None:
        active_config.trace_path = str(trace_path)
    if actions_path is not None:
        active_config.actions_path = str(actions_path)
    if goal is not None:
        active_config.goal = goal

    CittaRequestHandler.config = active_config
    server = ThreadingHTTPServer((host, port), CittaRequestHandler)
    print(f"Citta Console serving http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    run_server(config_path="examples/generic_jsonl/citta_config.json")
