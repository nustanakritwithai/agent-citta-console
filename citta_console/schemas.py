"""Shared schema objects for the Citta Console core.

The core intentionally keeps these objects small and serializable. Adapters can
translate framework-specific traces into these dataclasses or plain dicts.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Mapping
from uuid import uuid4


class AgentStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"


class PermissionLevel(str, Enum):
    SAFE = "safe"
    MEDIUM = "medium"
    DANGEROUS = "dangerous"
    FORBIDDEN = "forbidden"


class ActionStatus(str, Enum):
    PENDING_CONFIRMATION = "pending_confirmation"
    CONFIRMED = "confirmed"
    BLOCKED = "blocked"


class RiskSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


REQUIRED_EVENT_FIELDS = ("time", "task_id", "agent", "framework", "action", "status")
REQUIRED_ACTION_FIELDS = ("time", "action_id", "task_id", "action", "reason")


def now_iso() -> str:
    """Return an ISO-8601 UTC timestamp with seconds precision."""

    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def make_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:12]}"


@dataclass(slots=True)
class CittaEvent:
    time: str
    task_id: str
    agent: str
    framework: str
    action: str
    status: str
    event_id: str | None = None
    target: str | None = None
    input: Any | None = None
    output: Any | None = None
    error: Any | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        return {key: value for key, value in data.items() if value is not None}


@dataclass(slots=True)
class Risk:
    type: str
    severity: str
    reason: str
    event_id: str | None = None
    target: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        return {key: value for key, value in data.items() if value is not None}


@dataclass(slots=True)
class CittaAction:
    time: str
    action_id: str
    task_id: str
    action: str
    reason: str
    permission_level: str = PermissionLevel.SAFE.value
    status: str | None = None
    target: str | None = None
    params: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        return {key: value for key, value in data.items() if value is not None}


@dataclass(slots=True)
class RecommendedAction:
    action: str
    label: str
    permission_level: str
    reason: str
    target: str | None = None
    params: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        return {key: value for key, value in data.items() if value is not None}


@dataclass(slots=True)
class CittaReport:
    time: str
    task_id: str
    current_state: str
    active_agents: list[str]
    recent_events: int
    risks: list[dict[str, Any]]
    recommended_actions: list[dict[str, Any]]
    decision: str
    reason: str
    summary: str = ""
    events: list[dict[str, Any]] = field(default_factory=list)
    action_history: list[dict[str, Any]] = field(default_factory=list)
    goal: str | None = None

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        return {key: value for key, value in data.items() if value is not None}


def to_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    if hasattr(value, "to_dict"):
        return value.to_dict()
    if is_dataclass(value):
        return asdict(value)
    raise TypeError(f"Cannot convert {type(value).__name__} to dict")


def validate_event(data: Mapping[str, Any]) -> dict[str, Any]:
    missing = [field_name for field_name in REQUIRED_EVENT_FIELDS if not data.get(field_name)]
    if missing:
        raise ValueError(f"event missing required fields: {', '.join(missing)}")
    status = str(data["status"])
    if status not in {item.value for item in AgentStatus}:
        raise ValueError(f"unsupported event status: {status}")
    normalized = dict(data)
    metadata = normalized.get("metadata")
    normalized["metadata"] = metadata if isinstance(metadata, dict) else {}
    return normalized


def validate_action(data: Mapping[str, Any]) -> dict[str, Any]:
    missing = [field_name for field_name in REQUIRED_ACTION_FIELDS if not data.get(field_name)]
    if missing:
        raise ValueError(f"action missing required fields: {', '.join(missing)}")
    normalized = dict(data)
    normalized.setdefault("permission_level", PermissionLevel.SAFE.value)
    status = normalized.get("status")
    if status is not None and status not in {item.value for item in ActionStatus}:
        raise ValueError(f"unsupported action status: {status}")
    params = normalized.get("params")
    normalized["params"] = params if isinstance(params, dict) else {}
    return normalized


def event_from_dict(data: Mapping[str, Any]) -> CittaEvent:
    validated = validate_event(data)
    allowed = CittaEvent.__dataclass_fields__.keys()
    return CittaEvent(**{key: value for key, value in validated.items() if key in allowed})


def action_from_dict(data: Mapping[str, Any]) -> CittaAction:
    validated = validate_action(data)
    allowed = CittaAction.__dataclass_fields__.keys()
    return CittaAction(**{key: value for key, value in validated.items() if key in allowed})
