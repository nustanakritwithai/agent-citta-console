# MCP-style Foundation

v0.4 adds a local tool layer for exposing Citta operations to agent runtimes.

This is a local MCP-style foundation, not a complete MCP server yet.

The foundation is dependency-light and local-first:

- no external API calls
- no remote service integrations
- no shell execution
- no deploy execution
- no git push execution
- no delete execution
- no secret handling

## Tool dispatcher

Tools are defined in `citta_console.tools.definitions` and dispatched through
`citta_console.tools.dispatcher`.

```python
from citta_console.tools.dispatcher import dispatch_tool

result = dispatch_tool("citta.list_adapters", {})
```

Each tool definition includes:

- `name`
- `description`
- `input_schema`
- `output_schema`
- `safety_level`
- `handler`

## Built-in tools

- `citta.observe`
- `citta.render_dashboard`
- `citta.read_events`
- `citta.read_actions`
- `citta.write_action`
- `citta.list_adapters`
- `citta.describe_adapter`
- `citta.observe_with_adapter`

`citta.write_action` respects the existing permission layer. Forbidden actions
remain blocked by default. Medium and dangerous actions are recorded according
to the configured confirmation flow instead of being executed.

## CLI usage

```bash
citta-console tool citta.list_adapters
citta-console tool citta.describe_adapter --json '{"adapter":"generic"}'
citta-console tool citta.observe --json '{"trace_path":"examples/generic_jsonl/trace.jsonl","actions_path":"examples/generic_jsonl/actions.jsonl","dashboard_path":"examples/generic_jsonl/dashboard.html"}'
```

The CLI parses JSON input, calls the local dispatcher, prints JSON output, and
returns a nonzero exit code when a tool fails.

## Stdio skeleton

`citta_console/mcp_stdio.py` provides a minimal JSON-lines stdio skeleton for
future MCP work:

```json
{"tool":"citta.list_adapters","input":{}}
```

This skeleton is intentionally not documented as a complete MCP server. Full MCP
protocol compliance can be added later without changing the local tool handler
contract.

## Future direction

Future MCP work should wrap the local dispatcher with a complete MCP server
transport while preserving the same safety model: local traces and action
records first, no destructive execution in the core.
