"""JSON-style schemas for local Citta tool calls."""

from __future__ import annotations

from typing import Any


def object_schema(properties: dict[str, Any], required: list[str] | None = None) -> dict[str, Any]:
    return {
        "type": "object",
        "properties": properties,
        "required": required or [],
        "additionalProperties": True,
    }


OK_SCHEMA = {
    "ok": {"type": "boolean"},
}

PATH_PROPS = {
    "trace_path": {"type": "string"},
    "actions_path": {"type": "string"},
    "dashboard_path": {"type": "string"},
    "goal": {"type": ["string", "null"]},
    "task_id": {"type": ["string", "null"]},
}

OBSERVE_INPUT_SCHEMA = object_schema(
    PATH_PROPS,
    required=["trace_path", "actions_path", "dashboard_path"],
)
OBSERVE_OUTPUT_SCHEMA = object_schema(
    {
        **OK_SCHEMA,
        "report": {"type": "object"},
        "dashboard_path": {"type": "string"},
    },
    required=["ok", "report", "dashboard_path"],
)

RENDER_DASHBOARD_INPUT_SCHEMA = object_schema(
    {
        "trace_path": {"type": "string"},
        "actions_path": {"type": "string"},
        "dashboard_path": {"type": "string"},
    },
    required=["trace_path", "actions_path", "dashboard_path"],
)
RENDER_DASHBOARD_OUTPUT_SCHEMA = object_schema(
    {**OK_SCHEMA, "dashboard_path": {"type": "string"}},
    required=["ok", "dashboard_path"],
)

READ_EVENTS_INPUT_SCHEMA = object_schema(
    {"trace_path": {"type": "string"}, "limit": {"type": "integer"}},
    required=["trace_path"],
)
READ_EVENTS_OUTPUT_SCHEMA = object_schema(
    {**OK_SCHEMA, "events": {"type": "array"}},
    required=["ok", "events"],
)

READ_ACTIONS_INPUT_SCHEMA = object_schema(
    {"actions_path": {"type": "string"}, "limit": {"type": "integer"}},
    required=["actions_path"],
)
READ_ACTIONS_OUTPUT_SCHEMA = object_schema(
    {**OK_SCHEMA, "actions": {"type": "array"}},
    required=["ok", "actions"],
)

WRITE_ACTION_INPUT_SCHEMA = object_schema(
    {
        "actions_path": {"type": "string"},
        "action": {"type": "object"},
        "confirm": {"type": "boolean"},
    },
    required=["actions_path", "action"],
)
WRITE_ACTION_OUTPUT_SCHEMA = object_schema(
    {
        **OK_SCHEMA,
        "action_id": {"type": "string"},
        "status": {"type": "string"},
        "record": {"type": "object"},
    },
    required=["ok", "action_id"],
)

LIST_ADAPTERS_INPUT_SCHEMA = object_schema({})
LIST_ADAPTERS_OUTPUT_SCHEMA = object_schema(
    {**OK_SCHEMA, "adapters": {"type": "array"}},
    required=["ok", "adapters"],
)

DESCRIBE_ADAPTER_INPUT_SCHEMA = object_schema(
    {"adapter": {"type": "string"}},
    required=["adapter"],
)
DESCRIBE_ADAPTER_OUTPUT_SCHEMA = object_schema(
    {
        **OK_SCHEMA,
        "adapter": {"type": "string"},
        "description": {"type": "object"},
    },
    required=["ok", "adapter", "description"],
)

OBSERVE_WITH_ADAPTER_INPUT_SCHEMA = object_schema(
    {
        "adapter": {"type": "string"},
        "config_path": {"type": ["string", "null"]},
        "dashboard_path": {"type": "string"},
        "goal": {"type": ["string", "null"]},
        "task_id": {"type": ["string", "null"]},
    },
    required=["adapter", "dashboard_path"],
)
OBSERVE_WITH_ADAPTER_OUTPUT_SCHEMA = object_schema(
    {
        **OK_SCHEMA,
        "adapter": {"type": "string"},
        "report": {"type": "object"},
        "dashboard_path": {"type": "string"},
    },
    required=["ok", "adapter", "report", "dashboard_path"],
)

SUMMARIZE_REFLECTIONS_INPUT_SCHEMA = object_schema(
    {
        "reflections_path": {"type": "string"},
        "task_id": {"type": ["string", "null"]},
        "lesson_limit": {"type": "integer"},
        "mistake_limit": {"type": "integer"},
    },
    required=["reflections_path"],
)
SUMMARIZE_REFLECTIONS_OUTPUT_SCHEMA = object_schema(
    {
        **OK_SCHEMA,
        "memory": {"type": "object"},
    },
    required=["ok", "memory"],
)

RUN_REFLECTIVE_LOOP_INPUT_SCHEMA = object_schema(
    {
        **PATH_PROPS,
        "reflections_path": {"type": ["string", "null"]},
        "max_iterations": {"type": "integer"},
        "record_reflection": {"type": "boolean"},
        "fallback_action": {"type": "string"},
        "refresh_interval_seconds": {"type": "integer"},
    },
    required=["trace_path", "task_id"],
)
RUN_REFLECTIVE_LOOP_OUTPUT_SCHEMA = object_schema(
    {
        **OK_SCHEMA,
        "task_id": {"type": "string"},
        "iterations": {"type": "integer"},
        "stop_reason": {"type": "string"},
        "steps": {"type": "array"},
        "final_report": {"type": "object"},
        "trace_path": {"type": "string"},
        "reflections_path": {"type": "string"},
        "dashboard_path": {"type": ["string", "null"]},
    },
    required=["ok", "task_id", "iterations", "stop_reason", "steps", "final_report"],
)

RUN_REFLECTIVE_DAEMON_INPUT_SCHEMA = object_schema(
    {
        **PATH_PROPS,
        "reflections_path": {"type": ["string", "null"]},
        "poll_interval_seconds": {"type": "number"},
        "max_cycles": {"type": ["integer", "null"]},
        "record_reflection": {"type": "boolean"},
        "fallback_action": {"type": "string"},
        "refresh_interval_seconds": {"type": "integer"},
    },
    required=["trace_path", "task_id"],
)
RUN_REFLECTIVE_DAEMON_OUTPUT_SCHEMA = object_schema(
    {
        **OK_SCHEMA,
        "task_id": {"type": "string"},
        "stop_reason": {"type": "string"},
        "cycles": {"type": "integer"},
        "ticks_run": {"type": "integer"},
        "idle_polls": {"type": "integer"},
        "blocked": {"type": "boolean"},
        "history": {"type": "array"},
        "final_report": {"type": "object"},
        "trace_path": {"type": "string"},
        "reflections_path": {"type": "string"},
        "dashboard_path": {"type": ["string", "null"]},
        "poll_interval_seconds": {"type": "number"},
    },
    required=["ok", "task_id", "stop_reason", "cycles", "ticks_run", "history", "final_report"],
)
