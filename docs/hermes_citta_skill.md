# Hermes Citta Skill

The Hermes Citta Skill is an experimental local proof-of-concept for connecting
Hermes-style tasks to `agent-citta-console`.

It is a test skill, not a permanent Hermes runtime integration yet.

## Purpose

The skill lets a Hermes-like task write Citta-compatible JSONL events, then runs
Citta Console to generate an HTML dashboard with:

- current state
- detected risks
- recommended actions
- action history

Hermes remains the body/runtime. Citta Console observes traces and produces
dashboard insight.

## Trace flow

```text
Hermes-style activity
  -> trace_writer.py
  -> best-effort redaction
  -> citta_trace.jsonl
  -> Citta observer
  -> risk detector
  -> recommender
  -> dashboard.html
```

The skill records:

- user input as `user_input`
- tool calls as the tool name
- file edits as `edit_file`
- test results as `run_tests`
- final answers as `final_answer`

Each helper accepts optional `metadata` without changing the core Citta event
schema. Metadata is preserved in JSONL and can improve signal quality with
fields such as:

- `confidence`: numeric confidence for the event or answer
- `goal_alignment`: `low`, `medium`, `high`, or a numeric alignment score
- `reason`: short explanation for why the event may be risky
- `inspected_error`: whether the failed test/error was inspected before moving on
- `source_state`: local state label such as `test_failed_after_file_edit`
- `risk_hint`: optional hint such as `goal_drift_possible`
- `notes`: free-form local notes

Citta can use low `confidence`, low `goal_alignment`, or explicit `risk_hint`
metadata to detect `goal_drift_possible` and recommend `redirect`. For example,
if a task goal is "Improve UI and fix test failures" but the trace shows another
visual refactor after a failed test with `inspected_error=false`, the observer can
report goal drift without executing any action.

## Redaction / secret masking

Before JSONL trace writes, the trace writer applies a local, deterministic,
best-effort redaction pass. It masks common secret patterns in `input`, `output`,
`error`, metadata, and nested dict/list values. Secret-like values are replaced
with `[REDACTED]`.

Covered patterns include Authorization headers, bearer tokens, API key env-style
assignments, passwords, cookies, private key blocks, GitHub tokens, and nested
values whose key names include `api_key`, `token`, `secret`, `password`,
`cookie`, or `authorization`.

Redaction is best-effort, not a guarantee. Do not intentionally put secrets in
traces.

## Example command

```bash
python -m citta_console.skills.hermes_citta_skill.run_observer \
  --trace citta_console/skills/hermes_citta_skill/examples/citta_trace.jsonl \
  --actions citta_console/skills/hermes_citta_skill/examples/actions.jsonl \
  --dashboard citta_console/skills/hermes_citta_skill/examples/dashboard.html \
  --goal "Test Hermes Citta Skill" \
  --task-id "hermes_skill_test_001"
```

## Python import

```python
from citta_console.skills.hermes_citta_skill import HermesCittaSkill
```

## CLI command

```bash
citta-console hermes observe \
  --trace citta_console/skills/hermes_citta_skill/examples/citta_trace.jsonl \
  --actions citta_console/skills/hermes_citta_skill/examples/actions.jsonl \
  --dashboard citta_console/skills/hermes_citta_skill/examples/dashboard.html \
  --goal "Test Hermes Citta Skill" \
  --task-id "hermes_skill_test_001"
```

## Safety model

The skill:

- writes trace JSONL
- reads action history JSONL
- renders dashboard HTML
- reports risks and recommended action names

The skill does not:

- execute recommended actions
- modify Hermes runtime destructively
- call external APIs
- execute shell commands
- deploy
- git push
- delete files
- store secrets
- claim real consciousness

## Difference from full Hermes integration

A full bridge could later observe real Hermes runtime files, subscribe to
runtime events, and hand confirmed Citta action records back to Hermes.

This proof-of-concept only writes local Citta-compatible traces and runs the
existing Citta observer. It is intentionally small so the adapter and safety
contract can be reviewed first.
