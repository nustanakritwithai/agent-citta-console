#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

CONFIG="runtime/citta/citta_config.json"
TASK_ID="agent_main"
POLL_INTERVAL="${CITTA_POLL_INTERVAL:-2}"

python3 - <<'PY'
from citta_console.agent_runtime import ensure_runtime_layout, record_agent_event

ensure_runtime_layout()
record_agent_event(
    action="daemon_supervisor",
    target="scripts/citta_daemon_supervisor.sh",
    output="Citta supervisor started; reflective daemon will run continuously.",
    metadata={"role": "primary_system"},
)
PY

echo "[citta-supervisor] starting reflective daemon (task=${TASK_ID}, poll=${POLL_INTERVAL}s)"

while true; do
  python3 -m citta_console.cli loop daemon \
    --config "$CONFIG" \
    --task-id "$TASK_ID" \
    --poll-interval "$POLL_INTERVAL" || true
  echo "[citta-supervisor] daemon exited; restarting in 2s..." >&2
  sleep 2
done
