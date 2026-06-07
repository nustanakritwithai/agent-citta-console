"""agent-citta-console core package."""

from .analyzer import analyze_current_state
from .dispatcher import dispatch_action
from .observer import observe
from .recommender import recommend_actions
from .renderer import render_dashboard
from .risk_detector import detect_risks
from .trace_reader import read_recent_events, read_trace

__all__ = [
    "analyze_current_state",
    "detect_risks",
    "dispatch_action",
    "observe",
    "read_recent_events",
    "read_trace",
    "recommend_actions",
    "render_dashboard",
]

__version__ = "0.1.0"
