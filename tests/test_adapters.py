from pathlib import Path

from citta_console.adapters import (
    ClaudeCodeTranscriptAdapter,
    CodexTranscriptAdapter,
    GenericJsonlAdapter,
    HermesAdapter,
    OpenClawAdapter,
)
from citta_console.adapters.registry import get_adapter, list_adapters, register_adapter
from citta_console.observer import observe_with_adapter
from citta_console.schemas import CittaAction, now_iso


def _sample_action() -> CittaAction:
    return CittaAction(
        time=now_iso(),
        action_id="act_test",
        task_id="task_001",
        action="inspect_error",
        reason="Adapter contract test.",
        permission_level="safe",
        status="confirmed",
    )


def test_every_builtin_adapter_has_contract_methods() -> None:
    adapters = [
        GenericJsonlAdapter(),
        HermesAdapter(),
        OpenClawAdapter(),
        CodexTranscriptAdapter(),
        ClaudeCodeTranscriptAdapter(),
    ]

    for adapter in adapters:
        assert adapter.name
        assert callable(adapter.read_events)
        assert callable(adapter.read_actions)
        assert callable(adapter.write_action)
        assert callable(adapter.describe_source)
        assert adapter.describe_source()["name"] == adapter.name


def test_generic_adapter_reads_trace_and_writes_action(tmp_path: Path) -> None:
    trace_path = tmp_path / "trace.jsonl"
    actions_path = tmp_path / "actions.jsonl"
    trace_path.write_text(
        '{"time":"2026-06-07T16:00:00+07:00","task_id":"task_001","agent":"agent","framework":"generic","action":"edit_file","status":"completed"}\n',
        encoding="utf-8",
    )
    adapter = GenericJsonlAdapter(
        trace_path=trace_path,
        actions_path=actions_path,
        dashboard_path=tmp_path / "dashboard.html",
    )

    assert adapter.read_events()[0].task_id == "task_001"

    adapter.write_action(_sample_action())
    actions = adapter.read_actions()

    assert actions[0].action_id == "act_test"
    assert actions[0].action == "inspect_error"


def test_registry_lists_and_loads_adapters() -> None:
    names = list_adapters()

    assert {"generic", "hermes", "openclaw", "codex", "claude_code"}.issubset(names)
    assert get_adapter("generic").name == "generic"
    assert get_adapter("hermes").name == "hermes"


def test_registry_allows_custom_adapter_registration() -> None:
    class CustomAdapter(GenericJsonlAdapter):
        name = "custom"

    register_adapter("custom", CustomAdapter)

    assert get_adapter("custom").name == "custom"


def test_adapter_stubs_do_not_crash_on_basic_construction() -> None:
    assert OpenClawAdapter().read_events() == []
    assert HermesAdapter("missing-runtime").read_events() == []
    assert CodexTranscriptAdapter("missing.jsonl").read_events() == []
    assert ClaudeCodeTranscriptAdapter("missing.jsonl").read_events() == []


def test_hermes_adapter_reads_local_runtime_fixture() -> None:
    adapter = HermesAdapter("examples/hermes_like_runtime/runtime")
    events = adapter.read_events()

    assert len(events) == 2
    assert events[0].framework == "hermes"
    assert events[0].task_id == "task_001"
    assert events[1].status == "failed"


def test_transcript_adapters_read_local_fixtures() -> None:
    codex_events = CodexTranscriptAdapter("examples/transcripts/codex_transcript.jsonl").read_events()
    claude_events = ClaudeCodeTranscriptAdapter(
        "examples/transcripts/claude_code_transcript.jsonl"
    ).read_events()

    assert codex_events[0].framework == "codex"
    assert codex_events[0].action == "run_command"
    assert claude_events[0].framework == "claude_code"
    assert claude_events[0].action == "inspect_error"


def test_observe_with_adapter_builds_report_and_dashboard(tmp_path: Path) -> None:
    adapter = GenericJsonlAdapter(
        trace_path="examples/generic_jsonl/trace.jsonl",
        actions_path="examples/generic_jsonl/actions.jsonl",
        dashboard_path=tmp_path / "dashboard.html",
    )

    report = observe_with_adapter(adapter, tmp_path / "dashboard.html", goal="Adapter test")

    assert report["task_id"] == "task_001"
    assert report["recommended_actions"]
    assert (tmp_path / "dashboard.html").exists()
