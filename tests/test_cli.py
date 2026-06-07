import json

from citta_console.cli import main


def test_cli_returns_json_for_list_adapters(capsys) -> None:
    exit_code = main(["tool", "citta.list_adapters"])

    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == 0
    assert payload["ok"] is True
    assert "generic" in payload["adapters"]


def test_cli_accepts_json_input(capsys) -> None:
    exit_code = main(["tool", "citta.describe_adapter", "--json", '{"adapter":"generic"}'])

    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == 0
    assert payload["ok"] is True
    assert payload["adapter"] == "generic"


def test_cli_fails_cleanly_for_unknown_tool(capsys) -> None:
    exit_code = main(["tool", "citta.unknown"])

    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == 1
    assert payload["ok"] is False
    assert "unknown tool" in payload["error"]


def test_cli_rejects_invalid_json(capsys) -> None:
    exit_code = main(["tool", "citta.list_adapters", "--json", "{bad"])

    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == 2
    assert payload["ok"] is False
    assert "invalid JSON" in payload["error"]
