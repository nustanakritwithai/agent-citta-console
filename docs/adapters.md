# Adapters

The core only understands Citta schemas. Adapters translate framework-specific
runtime data into those schemas.

## Contract

Adapters implement `CittaAdapter` from `citta_console.adapters.base`:

```python
class CittaAdapter:
    name: str

    def read_events(self) -> list[CittaEvent]: ...
    def read_actions(self) -> list[CittaAction]: ...
    def write_action(self, action: CittaAction) -> None: ...
    def describe_source(self) -> dict: ...
```

Adapters should read local traces, transcripts, or runtime files and write Citta
action records. They should not execute shell commands, deploy, delete files, or
call external APIs.

## Registry

Built-in adapters can be loaded through the registry:

```python
from citta_console.adapters.registry import get_adapter
from citta_console.observer import observe_with_adapter

adapter = get_adapter("generic", config=config)
observe_with_adapter(adapter, dashboard_path="dashboard.html")
```

Built-in names:

- `generic`
- `hermes`
- `openclaw`
- `codex`
- `claude_code`

## Generic JSONL

The generic adapter reads `trace.jsonl`, reads/writes `actions.jsonl`, exposes a
source description, and supports config paths.

## Hermes

The v0.3 Hermes adapter is a local proof-of-concept only. It maps a
Hermes-like folder into Citta events:

- `runtime/tasks/`
- `runtime/events.jsonl`
- `runtime/actions.jsonl`
- `runtime/state.json`
- `runtime/result.md`

Missing files return empty lists instead of raising errors.

## OpenClaw

OpenClaw is represented by a contract-compliant stub in v0.3. Real workspace and
blackboard integration remains future adapter work.

## Codex / Claude Code

Codex and Claude Code adapters parse local JSONL or text transcript fixtures.
They do not call external APIs. Transcript records are mapped best-effort into
Citta events using fields such as time, task ID, action, target, status, output,
and error.

## Adding an adapter

1. Implement `CittaAdapter`.
2. Translate your runtime records into `CittaEvent`.
3. Write selected intentions as `CittaAction` records only.
4. Register it with `register_adapter(name, adapter_cls)`.
5. Add contract tests for construction, `read_events`, `read_actions`,
   `write_action`, and `describe_source`.
