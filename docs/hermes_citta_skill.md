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

## Example command

```bash
python skills/hermes_citta_skill/run_observer.py \
  --trace skills/hermes_citta_skill/examples/citta_trace.jsonl \
  --actions skills/hermes_citta_skill/examples/actions.jsonl \
  --dashboard skills/hermes_citta_skill/examples/dashboard.html \
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
