# agent-citta-console

A universal HTML control panel for agent awareness and action chaining.

Body agents act. Citta observes traces. The console decides what happens next.

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
examples/html_console_demo/dashboard.html
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

## Termux quickstart

```bash
pkg install python git
git clone https://github.com/yourname/agent-citta-console
cd agent-citta-console
pip install -e .
python examples/generic_jsonl/run_demo.py
```

The MVP uses the Python standard library at runtime.

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
- confirmation prompts for medium/dangerous actions
- action history

## Safety model

Actions are classified as:

- `safe`: inspect, view, summarize, read
- `medium`: run tests, pause, redirect, ask user
- `dangerous`: shell command, install, deploy, destructive file operations
- `forbidden`: project deletion, production deploy, external publishing

Every dispatched action must include a reason and is logged. Dangerous actions
require explicit confirmation. Forbidden actions are blocked by default.

## Adapter model

The core does not depend on any agent framework. Adapters should translate
runtime-specific logs, transcripts, task files, or blackboards into Citta events
and watch `actions.jsonl` or an API endpoint for selected actions.

The v0.1 MVP includes a generic JSONL adapter. Hermes, OpenClaw, Codex, and
Claude Code adapters are represented as extension points.

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
- better permission layer
- task filtering
- multi-agent view

### v0.3+

- Hermes and OpenClaw adapters
- Codex/Claude Code transcript adapters
- file diff and test failure viewers
- plugin system and custom risk rules

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
