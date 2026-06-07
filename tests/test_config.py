from pathlib import Path

import pytest

from citta_console.config import default_config, load_config


def test_default_config_has_expected_paths() -> None:
    config = default_config()

    assert config.trace_path == "examples/generic_jsonl/trace.jsonl"
    assert config.actions_path == "examples/generic_jsonl/actions.jsonl"
    assert config.refresh_interval_seconds == 5
    assert config.require_confirmation_for_medium is True


def test_load_config_overrides_defaults(tmp_path: Path) -> None:
    path = tmp_path / "citta_config.json"
    path.write_text(
        """
        {
          "trace_path": "trace.jsonl",
          "actions_path": "actions.jsonl",
          "dashboard_path": "dashboard.html",
          "refresh_interval_seconds": 0,
          "require_confirmation_for_medium": false
        }
        """,
        encoding="utf-8",
    )

    config = load_config(str(path))

    assert config.trace_path == "trace.jsonl"
    assert config.refresh_interval_seconds == 0
    assert config.require_confirmation_for_medium is False
    assert config.require_confirmation_for_dangerous is True


def test_load_config_rejects_unknown_key(tmp_path: Path) -> None:
    path = tmp_path / "citta_config.json"
    path.write_text('{"unknown": true}', encoding="utf-8")

    with pytest.raises(ValueError):
        load_config(str(path))
