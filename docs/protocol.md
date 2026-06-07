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

Optional action status values:

- `pending_confirmation`
- `confirmed`
- `blocked`

Safe actions are recorded as `confirmed`. Medium and dangerous actions are
recorded as `pending_confirmation` until a confirmation record is appended.
Forbidden actions are recorded as `blocked` by default.

Every action must be logged. No action record implies execution by the core
dispatcher; runtime adapters decide what to do with confirmed records.

## Report

A report is the Citta observer's current view:

- current state
- active agents
- recent event count
- risks
- recommended actions
- selected decision
- reason
