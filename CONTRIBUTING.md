# Contributing

Thank you for helping improve `agent-citta-console`.

## Project philosophy

Citta Console is a functional witness layer for autonomous agent systems. Body
agents act, traces remain, Citta observes, intention selects, and actions
continue.

This project does not claim to create real consciousness.

## Development setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

## Validation

Run these before opening a PR:

```bash
python3 -m pytest
python3 examples/generic_jsonl/run_demo.py
python3 -m compileall -q citta_console examples
```

## Adapter contribution rules

- Keep adapters framework-agnostic at the core boundary.
- Translate runtime data into Citta schemas.
- Prefer local files, traces, and transcripts for initial adapters.
- Do not call external APIs unless a future design explicitly allows it.
- Do not execute runtime actions from adapters.
- Add adapter contract tests.

## Tool contribution rules

- Keep tools local-first.
- Define input and output schemas.
- Add tests for handler and CLI behavior.
- `write_action`-style tools must respect the existing permission layer.

## Safety constraints

- No destructive actions by default.
- No shell execution inside runtime.
- No deploy/git push/delete execution.
- Forbidden actions stay blocked by default.
- Dangerous actions require confirmation.
- No secret handling unless explicitly designed and reviewed.

## Documentation expectations

- Update README or docs when behavior changes.
- Keep examples dependency-light.
- Be explicit when a feature is a local foundation rather than a complete
  external integration.
- Do not overclaim consciousness or awareness. Use the functional witness layer
  framing.
