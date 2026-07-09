# Hermes Runtime Trace Hook

The Hermes Runtime Trace Hook is an experimental, opt-in helper for capturing
Hermes-style runtime events as Citta-compatible JSONL trace events.

It is not full Hermes runtime integration. It does not patch the core runtime and
it must not be enabled for every task by default.

## Safety boundary

The hook writes trace events only. It does not execute recommended actions,
shell commands, deploys, git pushes, deletes, external API calls, or secret/token
handling. Recommendations such as `inspect_error`, `pause`, `run_tests`,
`view_diff`, and `redirect` remain reports for a human or a separate controller
to review.

The hook also makes no real consciousness claim. Terms such as `vipaka_check` are
used as local runtime trace labels only.

## Redaction / secret masking

Before a trace event is written to JSONL, Citta applies a local, deterministic,
best-effort redaction pass to `input`, `output`, `error`, `metadata`, and nested
values. Secret-like values are replaced with `[REDACTED]`.

The redactor masks common patterns such as Authorization headers, bearer tokens,
API-key environment assignments, passwords, cookies, private key blocks, GitHub
tokens, and nested values whose key names include `api_key`, `token`, `secret`,
`password`, `cookie`, or `authorization`.

Redaction is best-effort, not a guarantee. Do not intentionally put secrets in
traces. The runtime hook remains opt-in and disabled by default.

## Opt-in environment variables

Tracing is disabled unless explicitly enabled:

```bash
export HERMES_CITTA_TRACE_ENABLED=1
export HERMES_CITTA_TRACE_PATH=runtime/citta_trials/task_001/citta_trace.jsonl
export HERMES_CITTA_TASK_ID=task_001
```

Missing `HERMES_CITTA_TRACE_ENABLED` never auto-enables tracing. The accepted true
values are `1`, `true`, `yes`, and `on`.

## Python usage

```python
from citta_console.skills.hermes_citta_skill import HermesRuntimeTraceHook

hook = HermesRuntimeTraceHook(
    "runtime/citta_trials/task_001/citta_trace.jsonl",
    enabled=True,
    default_task_id="task_001",
    default_metadata={"notes": "controlled trial"},
)

hook.record_user_input("Improve UI and keep tests passing")
hook.record_file_edit(
    "src/ui.py",
    metadata={"confidence": 0.62, "goal_alignment": "medium"},
)
hook.record_command_result(
    "python -m pytest",
    status="failed",
    error="test_ui_render failed",
)
hook.record_vipaka_check("Risks reviewed; recommended actions recorded only")
```

Environment helper:

```python
from citta_console.skills.hermes_citta_skill import hook_from_env

hook = hook_from_env(default_metadata={"notes": "runtime trial"})
if hook.is_enabled():
    hook.record_user_input("Task text")
```

## Event mapping

- `record_user_input` -> `action=user_input`
- `record_tool_call(tool_name=...)` -> `action=<tool_name>`
- `record_file_edit` -> `action=edit_file`
- `record_command_result("python -m pytest", ...)` -> `action=run_tests`
- general `record_command_result` -> `action=command_result`
- `record_error` -> `action=error`, `status=failed`
- `record_final_answer` -> `action=final_answer`
- `record_vipaka_check` -> `action=vipaka_check`

## Metadata

Default metadata is merged with event metadata and caller metadata. Caller/event
metadata wins over default metadata. These signal keys are preserved inside the
JSONL event metadata when provided:

- `confidence`
- `goal_alignment`
- `reason`
- `inspected_error`
- `source_state`
- `risk_hint`
- `notes`

## Demo

```bash
python examples/hermes_runtime_hook/run_demo.py
python -m citta_console.cli hermes observe   --trace examples/hermes_runtime_hook/citta_trace.jsonl   --actions examples/hermes_runtime_hook/actions.jsonl   --dashboard examples/hermes_runtime_hook/dashboard.html   --goal "Hermes runtime hook demo"   --task-id "hermes_runtime_hook_demo_001"
```

Expected risk/action signals include:

- risks: `failed_event_detected`, `edit_after_failed_test`,
  `no_test_after_code_edit`, `goal_drift_possible`
- recommended actions: `inspect_error`, `pause`, `run_tests`, `view_diff`,
  `redirect`

## Limitations

- This is a controlled trace capture helper, not full Hermes runtime integration.
- It is disabled by default.
- It records only events provided by the caller.
- It does not execute recommended actions.
- Redaction is best-effort and not a guarantee; callers should not pass secrets
  into metadata, input, output, or error fields intentionally.
- It does not execute recommended actions.
