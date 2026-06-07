"""Tiny local HTTP server for the Citta Console MVP."""

from __future__ import annotations

import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from .dispatcher import dispatch_action
from .observer import observe
from .renderer import render_dashboard_html
from .storage import read_jsonl
from .trace_reader import events_to_dicts, filter_events_by_task, read_trace


class CittaRequestHandler(BaseHTTPRequestHandler):
    trace_path = Path("examples/generic_jsonl/trace.jsonl")
    actions_path = Path("examples/generic_jsonl/actions.jsonl")
    goal: str | None = None

    def _send(self, body: str, status: int = 200, content_type: str = "text/html") -> None:
        encoded = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", f"{content_type}; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def do_GET(self) -> None:  # noqa: N802 - http.server API
        parsed = urlparse(self.path)
        if parsed.path == "/":
            report = observe(
                self.trace_path,
                actions_path=self.actions_path,
                goal=self.goal,
            )
            self._send(render_dashboard_html(report))
            return
        if parsed.path.startswith("/task/"):
            task_id = parsed.path.removeprefix("/task/")
            report = observe(
                self.trace_path,
                task_id=task_id,
                actions_path=self.actions_path,
                goal=self.goal,
            )
            self._send(render_dashboard_html(report))
            return
        if parsed.path == "/actions":
            self._send(json.dumps(read_jsonl(self.actions_path), indent=2), content_type="application/json")
            return
        if parsed.path == "/trace":
            self._send(
                json.dumps(events_to_dicts(read_trace(self.trace_path)), indent=2),
                content_type="application/json",
            )
            return
        self._send("Not found", status=HTTPStatus.NOT_FOUND, content_type="text/plain")

    def do_POST(self) -> None:  # noqa: N802 - http.server API
        parsed = urlparse(self.path)
        if parsed.path != "/action":
            self._send("Not found", status=HTTPStatus.NOT_FOUND, content_type="text/plain")
            return

        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length).decode("utf-8")
        form = {key: values[0] for key, values in parse_qs(body).items()}
        task_id = form.get("task_id") or self._latest_task_id()
        confirm = form.get("confirm") in {"1", "true", "yes", "on"}
        try:
            record = dispatch_action(form, self.actions_path, task_id=task_id, confirm=confirm)
        except (PermissionError, ValueError) as exc:
            self._send(f"Action rejected: {exc}", status=HTTPStatus.BAD_REQUEST, content_type="text/plain")
            return
        self._send(
            "<html><body><h1>Action recorded</h1>"
            f"<pre>{json.dumps(record, indent=2)}</pre>"
            '<p><a href="/">Back to dashboard</a></p></body></html>'
        )

    def _latest_task_id(self) -> str:
        events = read_trace(self.trace_path)
        if not events:
            return "default"
        return events[-1].task_id


def run_server(
    host: str = "127.0.0.1",
    port: int = 8000,
    *,
    trace_path: str | Path = "examples/generic_jsonl/trace.jsonl",
    actions_path: str | Path = "examples/generic_jsonl/actions.jsonl",
    goal: str | None = None,
) -> None:
    CittaRequestHandler.trace_path = Path(trace_path)
    CittaRequestHandler.actions_path = Path(actions_path)
    CittaRequestHandler.goal = goal
    server = ThreadingHTTPServer((host, port), CittaRequestHandler)
    print(f"Citta Console serving http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    run_server()
