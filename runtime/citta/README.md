# Agent Citta Runtime

Persistent Citta witness layer for the Cursor cloud agent.

- **Config:** `citta_config.json`
- **Task id:** `agent_main`
- **Trace:** `trace.jsonl` (agent actions)
- **Reflections:** `reflections.jsonl` (observer records)
- **Dashboard:** `dashboard.html` (live HTML console)

## Start the always-on daemon

```bash
./scripts/citta_daemon_supervisor.sh
```

Or in tmux:

```bash
tmux new-session -d -s citta-core -c /workspace -- ./scripts/citta_daemon_supervisor.sh
```

## Check status

```bash
python3 -m citta_console.cli runtime status
```

## Record an agent action

```bash
python3 -m citta_console.cli runtime record \
  --action shell \
  --target "git status" \
  --status completed \
  --output "clean working tree"
```

The reflective daemon polls `trace.jsonl` and runs observe-reflect-act ticks
whenever new events appear.
