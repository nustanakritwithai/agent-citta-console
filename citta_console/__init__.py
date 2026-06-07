"""agent-citta-console core package."""

from .analyzer import analyze_current_state
from .config import default_config, load_config
from .dispatcher import dispatch_action
from .observer import observe, observe_with_adapter
from .recommender import recommend_actions
from .renderer import render_dashboard
from .risk_detector import detect_risks
from .tools import dispatch_tool, list_tool_definitions
from .trace_reader import read_recent_events, read_trace

__all__ = [
    "analyze_current_state",
    "detect_risks",
    "dispatch_action",
    "dispatch_tool",
    "default_config",
    "list_tool_definitions",
    "load_config",
    "observe",
    "observe_with_adapter",
    "read_recent_events",
    "read_trace",
    "recommend_actions",
    "render_dashboard",
]

__version__ = "0.7.0"
