# Architecture

```text
User Goal
  -> Agent Runtime
  -> Body Agents / Sub-agents
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
