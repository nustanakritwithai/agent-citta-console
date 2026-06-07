# Protocol

## Event

An event records one body-agent action. Events are stored as one JSON object per
line in `trace.jsonl`.

Required fields:

- `time`
- `task_id`
- `agent`
- `framework`
- `action`
- `status`

Supported statuses:

- `pending`
- `running`
- `completed`
- `failed`
- `blocked`
- `cancelled`

## Action

An action records an intention selected from the HTML console. Actions are
stored as one JSON object per line in `actions.jsonl`.

Required fields:

- `time`
- `action_id`
- `task_id`
- `action`
- `reason`

Every action must be logged. Dangerous actions require confirmation. Forbidden
actions are blocked by default.

## Report

A report is the Citta observer's current view:

- current state
- active agents
- recent event count
- risks
- recommended actions
- selected decision
- reason
