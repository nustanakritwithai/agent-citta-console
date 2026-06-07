# Architecture

```text
User Goal
  -> Agent Runtime
  -> Body Agents / Sub-agents
  -> citta_config.json
  -> trace.jsonl / logs / diffs / state
  -> Citta Observer
  -> State Analyzer
  -> Risk Detector
  -> Action Recommender
  -> HTML Renderer
  -> Citta Console HTML
  -> Action Button
  -> actions.jsonl / API / adapter
  -> Agent Runtime
```

The v0.1 implementation keeps the core framework-agnostic:

- `trace_reader.py` reads JSONL traces.
- `analyzer.py` summarizes current state.
- `risk_detector.py` detects basic failure and loop patterns.
- `recommender.py` maps state and risk to next actions.
- `renderer.py` creates the HTML dashboard.
- `dispatcher.py` appends selected actions to JSONL.
- `server.py` exposes the same flow through a local standard-library web server.

The v0.2 live console adds:

- `config.py` for trace, action, dashboard, refresh, and confirmation settings.
- auto-refresh HTML using a plain `<meta http-equiv="refresh">` tag.
- task detail routing through `GET /task/{task_id}`.
- confirmation routing for pending medium/dangerous actions.
- action history rendering from `actions.jsonl`.

The v0.4 MCP-style foundation adds:

- `citta_console.tools` for local tool definitions, schemas, handlers, and dispatch.
- `citta-console tool ...` for local JSON tool calls from agent runtimes.
- a minimal stdio JSON-lines skeleton for future MCP transport work.

This is a local MCP-style foundation, not a complete MCP server yet.
