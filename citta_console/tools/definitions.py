"""Tool definitions for the local Citta MCP-style foundation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from . import handlers, schemas


ToolHandler = Callable[[dict[str, Any]], dict[str, Any]]


@dataclass(frozen=True, slots=True)
class ToolDefinition:
    name: str
    description: str
    input_schema: dict[str, Any]
    output_schema: dict[str, Any]
    safety_level: str
    handler: ToolHandler

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema,
            "output_schema": self.output_schema,
            "safety_level": self.safety_level,
            "handler": self.handler.__name__,
        }


TOOLS: dict[str, ToolDefinition] = {
    "citta.observe": ToolDefinition(
        name="citta.observe",
        description="Observe a JSONL trace, build a report, and render a dashboard.",
        input_schema=schemas.OBSERVE_INPUT_SCHEMA,
        output_schema=schemas.OBSERVE_OUTPUT_SCHEMA,
        safety_level="safe",
        handler=handlers.handle_observe,
    ),
    "citta.render_dashboard": ToolDefinition(
        name="citta.render_dashboard",
        description="Render a dashboard from trace and action JSONL files.",
        input_schema=schemas.RENDER_DASHBOARD_INPUT_SCHEMA,
        output_schema=schemas.RENDER_DASHBOARD_OUTPUT_SCHEMA,
        safety_level="safe",
        handler=handlers.handle_render_dashboard,
    ),
    "citta.read_events": ToolDefinition(
        name="citta.read_events",
        description="Read recent Citta events from a JSONL trace.",
        input_schema=schemas.READ_EVENTS_INPUT_SCHEMA,
        output_schema=schemas.READ_EVENTS_OUTPUT_SCHEMA,
        safety_level="safe",
        handler=handlers.handle_read_events,
    ),
    "citta.read_actions": ToolDefinition(
        name="citta.read_actions",
        description="Read recent Citta action records from JSONL.",
        input_schema=schemas.READ_ACTIONS_INPUT_SCHEMA,
        output_schema=schemas.READ_ACTIONS_OUTPUT_SCHEMA,
        safety_level="safe",
        handler=handlers.handle_read_actions,
    ),
    "citta.write_action": ToolDefinition(
        name="citta.write_action",
        description="Append a Citta action record while respecting the permission layer.",
        input_schema=schemas.WRITE_ACTION_INPUT_SCHEMA,
        output_schema=schemas.WRITE_ACTION_OUTPUT_SCHEMA,
        safety_level="medium",
        handler=handlers.handle_write_action,
    ),
    "citta.list_adapters": ToolDefinition(
        name="citta.list_adapters",
        description="List registered Citta adapters.",
        input_schema=schemas.LIST_ADAPTERS_INPUT_SCHEMA,
        output_schema=schemas.LIST_ADAPTERS_OUTPUT_SCHEMA,
        safety_level="safe",
        handler=handlers.handle_list_adapters,
    ),
    "citta.describe_adapter": ToolDefinition(
        name="citta.describe_adapter",
        description="Describe a registered Citta adapter source.",
        input_schema=schemas.DESCRIBE_ADAPTER_INPUT_SCHEMA,
        output_schema=schemas.DESCRIBE_ADAPTER_OUTPUT_SCHEMA,
        safety_level="safe",
        handler=handlers.handle_describe_adapter,
    ),
    "citta.observe_with_adapter": ToolDefinition(
        name="citta.observe_with_adapter",
        description="Observe through a registered adapter and optionally render a dashboard.",
        input_schema=schemas.OBSERVE_WITH_ADAPTER_INPUT_SCHEMA,
        output_schema=schemas.OBSERVE_WITH_ADAPTER_OUTPUT_SCHEMA,
        safety_level="safe",
        handler=handlers.handle_observe_with_adapter,
    ),
    "citta.summarize_reflections": ToolDefinition(
        name="citta.summarize_reflections",
        description="Summarize prior lessons and mistakes from reflection JSONL history.",
        input_schema=schemas.SUMMARIZE_REFLECTIONS_INPUT_SCHEMA,
        output_schema=schemas.SUMMARIZE_REFLECTIONS_OUTPUT_SCHEMA,
        safety_level="safe",
        handler=handlers.handle_summarize_reflections,
    ),
}


def list_tool_definitions() -> list[dict[str, Any]]:
    return [tool.to_dict() for tool in TOOLS.values()]


def get_tool_definition(name: str) -> ToolDefinition:
    try:
        return TOOLS[name]
    except KeyError as exc:
        raise ValueError(f"unknown tool: {name}") from exc
