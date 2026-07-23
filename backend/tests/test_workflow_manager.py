from __future__ import annotations

import json

import pytest

from backend.core.conversation_models import Conversation, ConversationMessage
from backend.core.workflow_history_store import WorkflowHistoryStore
from backend.services.workflow_manager import WorkflowManager

WORKFLOW_ID = "youtube_production_v1"


class FakeConversationEngine:
    def __init__(self) -> None:
        self.appended: list[ConversationMessage] = []

    async def append_message(self, conversation_id: str, message: ConversationMessage) -> Conversation:
        self.appended.append(message)
        return None


class FakeWorkflowHistoryStore(WorkflowHistoryStore):
    def __init__(self) -> None:
        self.failed_calls: list[tuple[str, str]] = []

    async def record_started(self, execution_id, workflow_id, topic):
        raise NotImplementedError

    async def record_step_executed(self, execution_id, step_name):
        raise NotImplementedError

    async def record_failed(self, execution_id, failed_step):
        self.failed_calls.append((execution_id, failed_step))
        return None

    async def record_completed(self, execution_id, artifacts_generated, output_folder):
        raise NotImplementedError

    async def get(self, execution_id):
        raise NotImplementedError

    async def list_all(self):
        raise NotImplementedError


class FakeWorkflowEngine:
    def __init__(self, result: dict) -> None:
        self._result = result

    async def stream_execute(self, definition, *, topic, conversation_id, user_id):
        yield {"type": "progress", "text": "working..."}
        yield {"type": "result", "result": self._result}


def _write_export(output_folder, *, status: str, validation_errors: list[str] | None = None) -> None:
    output_folder.mkdir(parents=True, exist_ok=True)
    (output_folder / "summary.json").write_text(
        json.dumps({"status": status}), encoding="utf-8"
    )
    (output_folder / "workflow.json").write_text(
        json.dumps({"validation_errors": validation_errors or []}), encoding="utf-8"
    )


def _make_manager(engine_result: dict, history_store: FakeWorkflowHistoryStore) -> WorkflowManager:
    return WorkflowManager(
        llm_provider=None,
        conversation_engine=FakeConversationEngine(),
        workflow_engine=FakeWorkflowEngine(engine_result),
        workflow_factories={WORKFLOW_ID: lambda: object()},
        workflow_history_store=history_store,
    )


async def _drain(manager: WorkflowManager, conversation_id="conv-1", message="make a video"):
    events = []
    async for event in manager.stream_execute(
        conversation_id=conversation_id, message=message, topic="Dyatlov Incident", user_id=None
    ):
        events.append(event)
    return events


@pytest.mark.asyncio
async def test_stream_execute_reports_success_when_export_validation_passes(tmp_path):
    output_folder = tmp_path / "export"
    _write_export(output_folder, status="SUCCESS")
    engine_result = {
        "status": "success",
        "execution_id": "exec-1",
        "step_statuses": {"Research": "success"},
        "output_folder": str(output_folder),
        "files_written": ["research.md"],
    }
    history_store = FakeWorkflowHistoryStore()
    manager = _make_manager(engine_result, history_store)

    events = await _drain(manager)

    assert history_store.failed_calls == []
    assert events[-1]["event"] == "end"
    conversation_engine: FakeConversationEngine = manager._conversation_engine
    final_message = conversation_engine.appended[-1]
    assert final_message.metadata["status"] == "success"
    assert "Production complete" in final_message.content


@pytest.mark.asyncio
async def test_stream_execute_overrides_success_to_failed_on_export_validation_failure(tmp_path):
    output_folder = tmp_path / "export"
    _write_export(output_folder, status="FAILED", validation_errors=["missing required file: voice.mp3"])
    engine_result = {
        "status": "success",
        "execution_id": "exec-2",
        "step_statuses": {"Research": "success"},
        "output_folder": str(output_folder),
        "files_written": ["research.md"],
    }
    history_store = FakeWorkflowHistoryStore()
    manager = _make_manager(engine_result, history_store)

    events = await _drain(manager)

    assert history_store.failed_calls == [("exec-2", "Export Validation")]
    assert events[-1]["event"] == "end"
    conversation_engine: FakeConversationEngine = manager._conversation_engine
    final_message = conversation_engine.appended[-1]
    assert final_message.metadata["status"] == "failed"
    assert final_message.metadata["failed_step"] == "Export Validation"
    assert "missing required file: voice.mp3" in final_message.content


@pytest.mark.asyncio
async def test_stream_execute_treats_unreadable_summary_as_success(tmp_path):
    output_folder = tmp_path / "export"
    output_folder.mkdir(parents=True, exist_ok=True)
    # No summary.json written at all.
    engine_result = {
        "status": "success",
        "execution_id": "exec-3",
        "step_statuses": {"Research": "success"},
        "output_folder": str(output_folder),
        "files_written": ["research.md"],
    }
    history_store = FakeWorkflowHistoryStore()
    manager = _make_manager(engine_result, history_store)

    events = await _drain(manager)

    assert history_store.failed_calls == []
    conversation_engine: FakeConversationEngine = manager._conversation_engine
    final_message = conversation_engine.appended[-1]
    assert final_message.metadata["status"] == "success"


@pytest.mark.asyncio
async def test_stream_execute_handles_engine_level_failure_without_reading_export(tmp_path):
    engine_result = {
        "status": "failed",
        "execution_id": "exec-4",
        "failed_step": "Research",
        "error": "provider unavailable",
        "step_statuses": {"Research": "failed"},
    }
    history_store = FakeWorkflowHistoryStore()
    manager = _make_manager(engine_result, history_store)

    events = await _drain(manager)

    assert history_store.failed_calls == []
    conversation_engine: FakeConversationEngine = manager._conversation_engine
    final_message = conversation_engine.appended[-1]
    assert final_message.metadata["status"] == "failed"
    assert final_message.metadata["failed_step"] == "Research"
    assert events[-1]["event"] == "end"
