# Realistic Demo Walkthrough

The realistic demo shows what Citta Console is designed to notice: an agent
keeps changing UI code after a test failure instead of inspecting the root cause.

## Run the demo

```bash
python3 examples/realistic_demo/run_demo.py
```

Open:

```text
examples/realistic_demo/dashboard.html
```

You can also use the local tool CLI:

```bash
python3 -m citta_console.cli tool citta.observe --json '{"trace_path":"examples/realistic_demo/trace.jsonl","actions_path":"examples/realistic_demo/actions.jsonl","dashboard_path":"examples/realistic_demo/dashboard.html","goal":"Improve UI without ignoring test failures","task_id":"ui_refactor_001"}'
```

## Scenario

The task is `ui_refactor_001`: improve a dashboard UI without ignoring test
failures.

The trace simulates:

1. `code_agent` edits `src/ui.js` to improve the dashboard layout.
2. `test_agent` runs `python -m pytest` and reports
   `test_dashboard_rendering failed`.
3. `code_agent` keeps editing `src/renderer.py` without inspecting the failure.
4. `code_agent` changes styling before diagnosing the failing test.
5. `test_agent` sees the same dashboard rendering failure again.
6. `code_agent` edits the renderer again with low confidence.

## What Citta detects

Citta reads `trace.jsonl` and `actions.jsonl` rather than asking the body agents
to self-report. From the trace it can detect:

- a failed test event
- edits after a failed test
- code changes without a later passing test
- possible goal drift from low-confidence edits

## Why recommended actions appear

The recommended actions are derived from state and risk rules:

- `inspect_error` appears because a test failed and needs diagnosis.
- `pause` appears because edits continued after a failed test.
- `run_tests` appears because code changed and no later successful test is in
  the trace.
- `view_diff` can help inspect what changed before more edits happen.

## Body / Trace / Citta / Action loop

```text
Body agents act.
Traces remain.
Citta observes.
Intention selects.
Actions continue.
```

In this demo:

- Body agents: `code_agent`, `test_agent`
- Trace: `examples/realistic_demo/trace.jsonl`
- Citta: observer, analyzer, risk detector, recommender, renderer
- Actions: `examples/realistic_demo/actions.jsonl`
- Visual proof: `examples/realistic_demo/dashboard.html`

This demo is local fixture data only. It does not call external APIs or execute
shell, deploy, git push, or delete actions.
