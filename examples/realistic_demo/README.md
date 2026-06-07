# Realistic Demo

This demo shows an autonomous coding agent improving a UI, hitting a test
failure, and continuing to edit without inspecting the root cause.

Citta Console reads the trace and highlights:

- unresolved test failure
- edits after a failed test
- possible goal drift from low-confidence edits
- recommended next actions such as `inspect_error`, `pause`, and `run_tests`

Run:

```bash
python3 examples/realistic_demo/run_demo.py
```

Open:

```text
examples/realistic_demo/dashboard.html
```

Everything in this demo is local fixture data. It does not call external APIs or
execute shell, deploy, git push, or delete actions.
