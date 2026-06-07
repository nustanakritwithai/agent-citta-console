"""Best-effort local redaction for Citta trace events.

The redactor is deterministic and local-only. It masks common secret patterns
before JSONL trace writes, but callers should still avoid putting secrets into
traces intentionally.
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import Any

REDACTED = "[REDACTED]"

SECRET_KEY_HINTS = (
    "api_key",
    "apikey",
    "token",
    "secret",
    "password",
    "passwd",
    "pwd",
    "cookie",
    "authorization",
    "auth_header",
)

_PRIVATE_KEY_BLOCK_RE = re.compile(
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----",
    re.DOTALL,
)
_AUTH_BEARER_RE = re.compile(
    r"(?i)\b(Authorization\s*[:=]\s*Bearer\s+)([^\s\r\n;,'\"`]+)"
)
_AUTH_HEADER_RE = re.compile(
    r"(?i)\b(Authorization\s*[:=]\s*)(?!\s*Bearer\b)([^\r\n]+)"
)
_COOKIE_HEADER_RE = re.compile(r"(?i)\b(Cookie\s*[:=]\s*)([^\r\n]+)")
_ENV_SECRET_RE = re.compile(
    r"(?i)\b([A-Z0-9_]*(?:API[_-]?KEY|TOKEN|SECRET|PASSWORD|COOKIE|AUTHORIZATION)[A-Z0-9_]*\s*=\s*)([^\s\r\n;,'\"`]+)"
)
_GITHUB_TOKEN_RE = re.compile(
    r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,}\b"
)
_OPENAI_TOKEN_RE = re.compile(r"\bsk-[A-Za-z0-9][A-Za-z0-9_-]{8,}\b")
_GENERIC_SECRET_RE = re.compile(
    r"(?<![A-Za-z0-9_])[A-Za-z0-9_\-]{32,}\.[A-Za-z0-9_\-]{16,}\.[A-Za-z0-9_\-]{16,}(?![A-Za-z0-9_])"
)

SAFE_EVENT_IDENTITY_FIELDS = {"time", "event_id", "task_id", "agent", "framework", "action", "status"}


def redact_text(value: str) -> str:
    """Mask common secret patterns in a string."""

    redacted = _PRIVATE_KEY_BLOCK_RE.sub(REDACTED, value)
    redacted = _AUTH_BEARER_RE.sub(lambda match: f"{match.group(1)}{REDACTED}", redacted)
    redacted = _AUTH_HEADER_RE.sub(lambda match: f"{match.group(1)}{REDACTED}", redacted)
    redacted = _COOKIE_HEADER_RE.sub(lambda match: f"{match.group(1)}{REDACTED}", redacted)
    redacted = _ENV_SECRET_RE.sub(lambda match: f"{match.group(1)}{REDACTED}", redacted)
    redacted = _GITHUB_TOKEN_RE.sub(REDACTED, redacted)
    redacted = _OPENAI_TOKEN_RE.sub(REDACTED, redacted)
    redacted = _GENERIC_SECRET_RE.sub(REDACTED, redacted)
    return redacted


def redact_value(value: Any, *, key: str | None = None) -> Any:
    """Recursively redact a JSON-like value while preserving its shape."""

    if key is not None and _is_secret_key(key):
        if isinstance(value, Mapping):
            return {nested_key: REDACTED for nested_key in value}
        if _is_sequence_but_not_text(value):
            return [REDACTED for _ in value]
        if value is None:
            return None
        return REDACTED

    if isinstance(value, str):
        return redact_text(value)
    if isinstance(value, Mapping):
        return {item_key: redact_value(item_value, key=str(item_key)) for item_key, item_value in value.items()}
    if _is_sequence_but_not_text(value):
        return [redact_value(item) for item in value]
    return value


def redact_event(event: dict[str, Any]) -> dict[str, Any]:
    """Return a redacted copy of a Citta event dict."""

    return {key: redact_value(value, key=str(key)) for key, value in event.items()}


def _is_secret_key(key: str) -> bool:
    normalized = key.lower().replace("-", "_")
    return any(hint in normalized for hint in SECRET_KEY_HINTS)


def _is_sequence_but_not_text(value: Any) -> bool:
    return isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray))
