from pathlib import Path

from citta_console.storage import read_jsonl
from citta_console.tools import dispatch_tool, list_tool_definitions


def test_list_tool_definitions_contains_required_tools() -> None:
    names = {tool["name"] for tool in list_tool_definitions()}

    assert {
        "citta.observe",
        "citta.render_dashboard",
        "citta.read_events",
        "citta.read_actions",
        "citta.write_action",
        "citta.list_adapters",
        "citta.describe_adapter",
        "citta.observe_with_adapter",
        "citta.summarize_reflections",
        "citta.run_reflective_loop",
        "citta.run_reflective_daemon",
    }.issubset(names)


def test_dispatch_unknown_tool_returns_error() -> None:
    result = dispatch_tool("citta.unknown", {})

    assert result["ok"] is False
    assert "unknown tool" in result["error"]


def test_list_adapters_tool_works() -> None:
    result = dispatch_tool("citta.list_adapters", {})

    assert result["ok"] is True
    assert "generic" in result["adapters"]


def test_describe_adapter_tool_works() -> None:
    result = dispatch_tool("citta.describe_adapter", {"adapter": "generic"})

    assert result["ok"] is True
    assert result["adapter"] == "generic"
    assert result["description"]["name"] == "generic"


def test_observe_tool_generates_report_and_dashboard(tmp_path: Path) -> None:
    dashboard_path = tmp_path / "dashboard.html"

    result = dispatch_tool(
        "citta.observe",
        {
            "trace_path": "examples/generic_jsonl/trace.jsonl",
            "actions_path": "examples/generic_jsonl/actions.jsonl",
            "dashboard_path": str(dashboard_path),
            "goal": "Tool test",
        },
    )

    assert result["ok"] is True
    assert result["report"]["task_id"] == "task_001"
    assert dashboard_path.exists()


def test_render_dashboard_tool_generates_dashboard(tmp_path: Path) -> None:
    dashboard_path = tmp_path / "dashboard.html"

    result = dispatch_tool(
        "citta.render_dashboard",
        {
            "trace_path": "examples/generic_jsonl/trace.jsonl",
            "actions_path": "examples/generic_jsonl/actions.jsonl",
            "dashboard_path": str(dashboard_path),
        },
    )

    assert result == {"ok": True, "dashboard_path": str(dashboard_path)}
    assert dashboard_path.exists()


def test_read_events_and_actions_tools() -> None:
    events = dispatch_tool(
        "citta.read_events",
        {"trace_path": "examples/generic_jsonl/trace.jsonl", "limit": 1},
    )
    actions = dispatch_tool(
        "citta.read_actions",
        {"actions_path": "examples/generic_jsonl/actions.jsonl", "limit": 1},
    )

    assert events["ok"] is True
    assert len(events["events"]) == 1
    assert actions["ok"] is True
    assert isinstance(actions["actions"], list)


def test_write_action_tool_respects_permission_layer(tmp_path: Path) -> None:
    actions_path = tmp_path / "actions.jsonl"

    result = dispatch_tool(
        "citta.write_action",
        {
            "actions_path": str(actions_path),
            "action": {
                "task_id": "task_001",
                "action": "inspect_error",
                "target": "latest_failed_test",
                "reason": "Inspect failed test before continuing",
                "permission_level": "safe",
            },
        },
    )

    assert result["ok"] is True
    assert result["action_id"]
    assert read_jsonl(actions_path)[0]["status"] == "confirmed"


def test_write_action_tool_blocks_forbidden_action(tmp_path: Path) -> None:
    actions_path = tmp_path / "actions.jsonl"

    result = dispatch_tool(
        "citta.write_action",
        {
            "actions_path": str(actions_path),
            "action": {
                "task_id": "task_001",
                "action": "delete_project",
                "reason": "Unsafe request",
            },
        },
    )

    assert result["ok"] is True
    assert result["status"] == "blocked"
    assert read_jsonl(actions_path)[0]["permission_level"] == "forbidden"


def test_observe_with_adapter_tool_generates_dashboard(tmp_path: Path) -> None:
    dashboard_path = tmp_path / "adapter_dashboard.html"

    result = dispatch_tool(
        "citta.observe_with_adapter",
        {
            "adapter": "generic",
            "config_path": "examples/generic_jsonl/citta_config.json",
            "dashboard_path": str(dashboard_path),
            "goal": "Adapter tool test",
        },
    )

    assert result["ok"] is True
    assert result["adapter"] == "generic"
    assert result["report"]["task_id"] == "task_001"
    assert dashboard_path.exists()
