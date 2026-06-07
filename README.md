# agent-citta-console

[![CI](https://github.com/nustanakritwithai/agent-citta-console/actions/workflows/ci.yml/badge.svg)](https://github.com/nustanakritwithai/agent-citta-console/actions/workflows/ci.yml)

A universal HTML control panel for agent awareness and action chaining.

Body agents act. Citta observes traces. The console decides what happens next.

Project status: early local-first releases. The core JSONL protocol, HTML
console, adapter foundation, and local MCP-style tool dispatcher are available.

## What is it?

`agent-citta-console` is a small Python project that reads agent activity from a
generic JSONL trace, analyzes the current state, detects simple risks,
recommends next actions, renders an HTML dashboard, and records selected
actions to `actions.jsonl`.

It is designed as a framework-agnostic "functional witness layer" for
autonomous agent systems. Body agents do their work and leave traces; Citta
Console observes those traces and exposes a human-readable control panel.

## Why it exists

Agent systems often spread useful state across logs, diffs, command output,
task files, and partial memories. Citta Console provides a common surface for:

- current state
- active agents
- recent actions
- detected risks
- suggested next actions
- action buttons
- permission warnings
- action history

## Core idea

```text
Body agents act.
Traces remain.
Citta observes.
Intention selects.
Actions continue.
```

Thai summary:

```text
กายทำงาน
กรรมทิ้งร่องรอย
จิตเข้าไปรู้
เจตนาเลือกทาง
กายทำกรรมต่อ
```

## How it works

```text
trace.jsonl
  -> trace_reader
  -> analyzer
  -> risk_detector
  -> recommender
  -> renderer
  -> dashboard.html
  -> dispatcher
  -> actions.jsonl
```

The core only understands Citta event/action/report schemas. Runtime-specific
systems such as Hermes, OpenClaw, Codex, or Claude Code should integrate through
adapters that translate their traces into the common schema.

## Quickstart

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
python examples/generic_jsonl/run_demo.py
```

Open:

```text
examples/generic_jsonl/dashboard.html
```

The demo reads `examples/generic_jsonl/citta_config.json` for trace, action,
dashboard, and auto-refresh settings.

## Install from GitHub

```bash
python -m pip install "agent-citta-console @ git+https://github.com/nustanakritwithai/agent-citta-console.git"
```

For development:

```bash
git clone https://github.com/nustanakritwithai/agent-citta-console
cd agent-citta-console
python -m pip install -e ".[dev]"
```

Run tests:

```bash
pytest
```

Run the local standard-library server:

```bash
python examples/html_console_demo/demo_server.py
```

Then visit `http://127.0.0.1:8000`.

Live console routes:

- `GET /` for the auto-refresh dashboard
- `GET /task/{task_id}` for a task detail page
- `GET /actions` for JSON action history
- `POST /action` to record a selected action
- `GET /confirm?action_id=...`, `POST /confirm`, and `POST /cancel` for confirmation flow

## CLI quickstart

```bash
citta-console tool citta.list_adapters
citta-console tool citta.describe_adapter --json '{"adapter":"generic"}'
citta-console tool citta.read_events --json '{"trace_path":"examples/generic_jsonl/trace.jsonl","limit":5}'
```

Tool calls return JSON and run local Citta functions only.

## Demo screenshots

To capture a screenshot:

1. Run `python examples/generic_jsonl/run_demo.py`.
2. Open `examples/generic_jsonl/dashboard.html` in a browser.
3. Capture the browser window with your OS screenshot tool.

Screenshots are documentation artifacts and are not required for tests.

## Termux quickstart

```bash
pkg install python git
git clone https://github.com/nustanakritwithai/agent-citta-console
cd agent-citta-console
pip install -e .
python examples/generic_jsonl/run_demo.py
```

The MVP uses the Python standard library at runtime.

## Config file

The local console can be configured with JSON:

```json
{
  "trace_path": "examples/generic_jsonl/trace.jsonl",
  "actions_path": "examples/generic_jsonl/actions.jsonl",
  "dashboard_path": "examples/generic_jsonl/dashboard.html",
  "refresh_interval_seconds": 5,
  "require_confirmation_for_medium": true,
  "require_confirmation_for_dangerous": true,
  "block_forbidden_actions": true
}
```

## Event schema

Each trace event is one JSON object per line in `trace.jsonl`:

```json
{
  "time": "2026-06-07T15:00:00+07:00",
  "event_id": "evt_001",
  "task_id": "task_001",
  "agent": "code_agent",
  "framework": "generic",
  "action": "edit_file",
  "target": "src/ui.js",
  "status": "completed",
  "input": "Improve hex map UI",
  "output": "Edited map rendering logic",
  "error": null,
  "metadata": {
    "cwd": "/project",
    "tool": "edit",
    "files_changed": ["src/ui.js"],
    "confidence": 0.74
  }
}
```

Required fields: `time`, `task_id`, `agent`, `framework`, `action`, `status`.

Supported statuses: `pending`, `running`, `completed`, `failed`, `blocked`,
`cancelled`.

## Action schema

Each selected action is appended to `actions.jsonl`:

```json
{
  "time": "2026-06-07T15:05:00+07:00",
  "action_id": "act_001",
  "task_id": "task_001",
  "action": "inspect_error",
  "target": "latest_failed_test",
  "reason": "Test failed after UI edit",
  "permission_level": "safe",
  "status": "confirmed",
  "params": {
    "source": "trace.jsonl"
  }
}
```

Core actions include `continue`, `pause`, `stop`, `inspect_error`, `run_tests`,
`view_diff`, `summarize_state`, `ask_user`, `redirect`, `rollback`, `approve`,
and `reject`.

## HTML console

The dashboard includes:

- header with task, goal, and current status
- current state summary
- active agents
- recent trace table
- risks with severity
- recommended action buttons
- confirmation flow for medium/dangerous actions
- action history
- auto-refresh status

## Safety model

Actions are classified as:

- `safe`: inspect, view, summarize, read
- `medium`: run tests, pause, redirect, ask user
- `dangerous`: shell command, install, deploy, destructive file operations
- `forbidden`: project deletion, production deploy, external publishing

Every dispatched action must include a reason and is logged. Medium and
dangerous actions are recorded as `pending_confirmation` before they can be
confirmed. Forbidden actions are blocked by default. The MVP does not execute
shell, deploy, git push, or delete operations.

## Adapter model

The core does not depend on any agent framework. Adapters should translate
runtime-specific logs, transcripts, task files, or blackboards into Citta events
and watch `actions.jsonl` or an API endpoint for selected actions.

The adapter contract is:

```python
class CittaAdapter:
    name: str

    def read_events(self) -> list[CittaEvent]: ...
    def read_actions(self) -> list[CittaAction]: ...
    def write_action(self, action: CittaAction) -> None: ...
    def describe_source(self) -> dict: ...
```

Example:

```python
from citta_console.adapters.registry import get_adapter
from citta_console.observer import observe_with_adapter

adapter = get_adapter("generic", config=config)
observe_with_adapter(adapter, dashboard_path="dashboard.html")
```

The v0.3 foundation includes a generic JSONL adapter, a Hermes-like local
runtime proof-of-concept, OpenClaw as a contract-compliant stub, and local
transcript mock adapters for Codex and Claude Code. These adapters do not call
external APIs or execute runtime actions.

## Local MCP-style tools

v0.4 exposes Citta operations through a local tool dispatcher and CLI.

This is a local MCP-style foundation, not a complete MCP server yet.

Examples:

```bash
citta-console tool citta.list_adapters
citta-console tool citta.describe_adapter --json '{"adapter":"generic"}'
citta-console tool citta.observe --json '{"trace_path":"examples/generic_jsonl/trace.jsonl","actions_path":"examples/generic_jsonl/actions.jsonl","dashboard_path":"examples/generic_jsonl/dashboard.html"}'
```

Built-in tools include:

- `citta.observe`
- `citta.render_dashboard`
- `citta.read_events`
- `citta.read_actions`
- `citta.write_action`
- `citta.list_adapters`
- `citta.describe_adapter`
- `citta.observe_with_adapter`

The tool dispatcher calls local Citta functions only. It does not call external
APIs or execute shell, deploy, git push, or delete operations.

## Release history

See [CHANGELOG.md](CHANGELOG.md).

## What this is not

- Not a claim of real consciousness.
- Not a remote MCP server with full protocol compliance.
- Not a deployment, git, shell, or file deletion executor.
- Not a deep integration with Hermes, OpenClaw, Codex, or Claude Code yet.
- Not a replacement for runtime-specific safety review.

## Roadmap

### v0.1

- Generic JSONL trace
- HTML dashboard
- action buttons
- `actions.jsonl` dispatcher
- basic risk detection

### v0.2

- local server improvements
- auto-refresh dashboard
- config file for paths and live-console behavior
- confirmation flow for medium/dangerous actions
- action history panel
- task detail page
- task filtering

### v0.3

- stable adapter contract
- adapter registry
- improved generic adapter
- Hermes-like local runtime proof-of-concept
- Codex/Claude Code transcript mock adapters
- adapter contract tests

### v0.4

- local MCP-style tool definitions
- local tool dispatcher
- CLI entrypoint for tool calls
- stdio JSON-lines skeleton for future MCP work
- tool dispatcher tests

### v0.5+

- file diff and test failure viewers
- plugin system and custom risk rules
- deeper framework adapters

## Philosophy

`agent-citta-console` uses the metaphor of body agents and a witness layer:

- sub-agent = body
- trace = past action
- Citta Observer = functional witness
- HTML dashboard = observed state
- action button = new intention
- dispatcher = intention becoming action

## Disclaimer

This project does not claim to create real consciousness.

It models the functional role of a witness/awareness layer in autonomous agent
systems: reading traces, summarizing state, detecting risks, and selecting next
actions through an HTML interface.
