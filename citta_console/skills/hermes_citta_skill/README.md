# Hermes Citta Skill

Experimental local skill for connecting Hermes-style tasks to
`agent-citta-console`.

Hermes remains the body/runtime. Citta Console observes traces and produces
dashboard insight.

This skill:

- records Hermes activity as Citta Event JSONL
- generates an HTML dashboard
- reports risks and recommendations

This skill does not:

- execute recommended actions
- modify Hermes runtime
- call external APIs
- create real consciousness

## Run the observer demo

```bash
python -m citta_console.skills.hermes_citta_skill.run_observer \
  --trace citta_console/skills/hermes_citta_skill/examples/citta_trace.jsonl \
  --actions citta_console/skills/hermes_citta_skill/examples/actions.jsonl \
  --dashboard citta_console/skills/hermes_citta_skill/examples/dashboard.html \
  --goal "Test Hermes Citta Skill" \
  --task-id "hermes_skill_test_001"
```

Or through the installed CLI:

```bash
citta-console hermes observe \
  --trace citta_console/skills/hermes_citta_skill/examples/citta_trace.jsonl \
  --actions citta_console/skills/hermes_citta_skill/examples/actions.jsonl \
  --dashboard citta_console/skills/hermes_citta_skill/examples/dashboard.html \
  --goal "Test Hermes Citta Skill" \
  --task-id "hermes_skill_test_001"
```

Open:

```text
citta_console/skills/hermes_citta_skill/examples/dashboard.html
```

Expected detected risks:

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

Everything here is local fixture data. This is not a full Hermes runtime
integration yet.
