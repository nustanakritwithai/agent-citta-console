"""Configuration for the local Citta Console."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class CittaConfig:
    trace_path: str = "examples/generic_jsonl/trace.jsonl"
    actions_path: str = "examples/generic_jsonl/actions.jsonl"
    dashboard_path: str = "examples/generic_jsonl/dashboard.html"
    refresh_interval_seconds: int = 5
    require_confirmation_for_medium: bool = True
    require_confirmation_for_dangerous: bool = True
    block_forbidden_actions: bool = True
    goal: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def default_config() -> CittaConfig:
    return CittaConfig()


def _coerce_bool(value: Any, field_name: str) -> bool:
    if isinstance(value, bool):
        return value
    raise ValueError(f"{field_name} must be a boolean")


def _coerce_int(value: Any, field_name: str) -> int:
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    raise ValueError(f"{field_name} must be an integer")


def load_config(path: str | None = None) -> CittaConfig:
    config = default_config()
    if path is None:
        return config

    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"config file not found: {config_path}")

    with config_path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError("config file must contain a JSON object")

    data = config.to_dict()
    for key, value in payload.items():
        if key not in data:
            raise ValueError(f"unknown config key: {key}")
        data[key] = value

    for key in ("trace_path", "actions_path", "dashboard_path"):
        if not isinstance(data[key], str) or not data[key]:
            raise ValueError(f"{key} must be a non-empty string")
    data["refresh_interval_seconds"] = _coerce_int(
        data["refresh_interval_seconds"], "refresh_interval_seconds"
    )
    if data["refresh_interval_seconds"] < 0:
        raise ValueError("refresh_interval_seconds must be >= 0")
    for key in (
        "require_confirmation_for_medium",
        "require_confirmation_for_dangerous",
        "block_forbidden_actions",
    ):
        data[key] = _coerce_bool(data[key], key)
    if data["goal"] is not None and not isinstance(data["goal"], str):
        raise ValueError("goal must be a string or null")

    return CittaConfig(**data)
