"""Local MCP-style tool foundation for Citta Console."""

from .definitions import ToolDefinition, get_tool_definition, list_tool_definitions
from .dispatcher import dispatch_tool, require_tool_success

__all__ = [
    "ToolDefinition",
    "dispatch_tool",
    "get_tool_definition",
    "list_tool_definitions",
    "require_tool_success",
]
