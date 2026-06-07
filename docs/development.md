# Development Guide

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

## Running tests

```bash
python3 -m pytest
```

## Running the demo

```bash
python3 examples/generic_jsonl/run_demo.py
```

Open:

```text
examples/generic_jsonl/dashboard.html
```

## Compile check

```bash
python3 -m compileall -q citta_console examples
```

## CLI tools

```bash
citta-console tool citta.list_adapters
citta-console tool citta.describe_adapter --json '{"adapter":"generic"}'
citta-console tool citta.read_events --json '{"trace_path":"examples/generic_jsonl/trace.jsonl","limit":5}'
```

## Adding adapters

1. Implement `CittaAdapter`.
2. Read local traces, transcripts, or runtime files.
3. Convert records into `CittaEvent`.
4. Write selected intentions as `CittaAction` records only.
5. Register the adapter.
6. Add adapter contract tests.

Adapters should not call external APIs or execute runtime actions.

## Adding tools

1. Add input/output schemas in `citta_console/tools/schemas.py`.
2. Add a local handler in `citta_console/tools/handlers.py`.
3. Register a definition in `citta_console/tools/definitions.py`.
4. Add tests in `tests/test_tools.py` and CLI coverage if needed.

Tools should call local Citta functions only.

## Safety rules

- Keep runtime local-first.
- Do not add shell execution inside runtime.
- Do not add deploy/git push/delete execution.
- Do not add secret handling.
- Do not add external service calls without an explicit future design.
- Keep dangerous actions behind confirmation and forbidden actions blocked by default.
- Keep the project framed as a functional witness layer.
- Do not claim the project creates real consciousness.
