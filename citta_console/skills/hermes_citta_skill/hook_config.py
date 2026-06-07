"""Environment config helper for the opt-in Hermes runtime trace hook."""

from __future__ import annotations

import os
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from .runtime_hook import HermesRuntimeTraceHook

TRUE_VALUES = {"1", "true", "yes", "on"}


def hook_config_from_env(env: Mapping[str, str] | None = None) -> dict[str, Any]:
    """Read safe opt-in hook config from environment variables.

    The hook is disabled unless HERMES_CITTA_TRACE_ENABLED is explicitly set to
    one of: 1, true, yes, on. Missing env never auto-enables tracing.
    """

    source = env if env is not None else os.environ
    enabled = str(source.get("HERMES_CITTA_TRACE_ENABLED", "")).strip().lower() in TRUE_VALUES
    trace_path = source.get("HERMES_CITTA_TRACE_PATH", "runtime/citta_trials/task_001/citta_trace.jsonl")
    task_id = source.get("HERMES_CITTA_TASK_ID")
    return {
        "enabled": enabled,
        "trace_path": Path(trace_path),
        "default_task_id": task_id,
    }


def hook_from_env(
    env: Mapping[str, str] | None = None,
    *,
    default_metadata: dict[str, Any] | None = None,
) -> HermesRuntimeTraceHook:
    """Create a HermesRuntimeTraceHook from opt-in environment config."""

    config = hook_config_from_env(env)
    return HermesRuntimeTraceHook(
        config["trace_path"],
        enabled=config["enabled"],
        default_task_id=config["default_task_id"],
        default_metadata=default_metadata,
    )
