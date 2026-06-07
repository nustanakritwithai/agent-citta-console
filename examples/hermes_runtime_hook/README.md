# Hermes Runtime Hook Demo

This demo uses `HermesRuntimeTraceHook` in explicit opt-in mode (`enabled=True`)
to write a controlled Citta-compatible JSONL trace.

It simulates a realistic Hermes task:

1. user asks to improve UI while keeping tests passing
2. a UI file edit is recorded
3. `python -m pytest` is recorded as failed
4. another UI edit is recorded without inspecting the error
5. final answer is recorded
6. Citta observer renders `dashboard.html`

The demo prints detected risks and recommended actions. Recommended actions are
reported only; they are not executed.

Run:

```bash
python examples/hermes_runtime_hook/run_demo.py
```

Run the CLI observer explicitly:

```bash
python -m citta_console.cli hermes observe   --trace examples/hermes_runtime_hook/citta_trace.jsonl   --actions examples/hermes_runtime_hook/actions.jsonl   --dashboard examples/hermes_runtime_hook/dashboard.html   --goal "Hermes runtime hook demo"   --task-id "hermes_runtime_hook_demo_001"
```

Expected risks:

- `failed_event_detected`
- `edit_after_failed_test`
- `no_test_after_code_edit`
- `goal_drift_possible`

Expected recommended actions:

- `inspect_error`
- `pause`
- `run_tests`
- `view_diff`
- `redirect`
