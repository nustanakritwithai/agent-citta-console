# Adapters

The core only understands Citta schemas. Adapters translate framework-specific
runtime data into those schemas.

## Generic JSONL

The v0.1 adapter reads `trace.jsonl`, writes `actions.jsonl`, and renders
`dashboard.html`.

## Hermes

Planned inputs:

- `runtime/tasks/`
- `runtime/events.jsonl`
- `runtime/messages.jsonl`
- `runtime/state.json`
- `runtime/result.md`

## OpenClaw

Planned inputs:

- task trace
- workspace state
- blackboard
- worker messages

## Codex / Claude Code

The first integration target should be transcript adapters. They can convert
commands, results, and file edits into Citta events and produce `next_action.md`
or prompt text as adapter output.
