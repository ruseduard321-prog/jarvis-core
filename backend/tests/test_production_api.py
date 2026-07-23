from __future__ import annotations

from datetime import datetime

import pytest

from backend.api.v1.production import _response_from_history_record, _run_production_in_background
from backend.core.task_manager import BackgroundTaskManager, InMemoryTaskBackend
from backend.core.task_models import TaskStatus
from backend.core.workflow_history_store import WorkflowHistoryRecord


def _record(**overrides) -> WorkflowHistoryRecord:
    defaults = dict(
        execution_id="exec-1",
        workflow_id="youtube_production_v1",
        topic="Test Topic",
        status="running",
        started_at=datetime(2026, 1, 1),
    )
    defaults.update(overrides)
    return WorkflowHistoryRecord(**defaults)


def test_response_from_history_record_maps_running_state():
    record = _record(status="running", steps_executed=["Research", "Strategy"])

    response = _response_from_history_record("exec-1", record)

    assert response.status == "running"
    assert response.step_statuses == {"Research": "success", "Strategy": "success"}
    assert response.failed_step is None
    assert response.error is None


def test_response_from_history_record_maps_success_state():
    record = _record(
        status="success",
        steps_executed=["Research", "Strategy"],
        artifacts_generated=["research.md", "strategy.md"],
        output_folder="/fake/output",
    )

    response = _response_from_history_record("exec-1", record)

    assert response.status == "success"
    assert response.output_folder == "/fake/output"
    assert response.files_written == ["research.md", "strategy.md"]


def test_response_from_history_record_maps_failed_state_with_failed_step():
    record = _record(status="failed", steps_executed=["Research"], failed_step="Strategy")

    response = _response_from_history_record("exec-1", record)

    assert response.status == "failed"
    assert response.step_statuses == {"Research": "success", "Strategy": "failed"}
    assert response.failed_step == "Strategy"
    assert response.error == "Step 'Strategy' failed"


class FakeWorkflowDefinition:
    id = "youtube_production_v1"


class FakeWorkflowEngine:
    def __init__(self, *, final_status: str = "success", raises: Exception | None = None):
        self._final_status = final_status
        self._raises = raises
        self.called_with: dict | None = None

    async def stream_execute(self, definition, *, topic, conversation_id, user_id, execution_id=None):
        self.called_with = {
            "definition": definition,
            "topic": topic,
            "conversation_id": conversation_id,
            "user_id": user_id,
            "execution_id": execution_id,
        }
        if self._raises:
            raise self._raises
        yield {"type": "progress", "text": "started"}
        yield {"type": "result", "result": {"status": self._final_status, "execution_id": execution_id}}


@pytest.mark.asyncio
async def test_run_production_in_background_marks_task_succeeded_on_success():
    task_manager = BackgroundTaskManager(InMemoryTaskBackend())
    task = await task_manager.submit("youtube_production_run", {"topic": "Test"})
    engine = FakeWorkflowEngine(final_status="success")

    await _run_production_in_background(
        workflow_engine=engine,
        workflow_definition=FakeWorkflowDefinition(),
        task_manager=task_manager,
        execution_id=task.id,
        topic="Test Topic",
        user_id="user-1",
    )

    final_task = await task_manager.get(task.id)
    assert final_task.status == TaskStatus.SUCCEEDED
    # F1: the pre-generated task.id is threaded through as the workflow's own
    # execution_id, so status lookups by the same id work end to end.
    assert engine.called_with["execution_id"] == task.id
    assert engine.called_with["user_id"] == "user-1"


@pytest.mark.asyncio
async def test_run_production_in_background_marks_task_failed_on_failed_workflow_status():
    task_manager = BackgroundTaskManager(InMemoryTaskBackend())
    task = await task_manager.submit("youtube_production_run", {"topic": "Test"})
    engine = FakeWorkflowEngine(final_status="failed")

    await _run_production_in_background(
        workflow_engine=engine,
        workflow_definition=FakeWorkflowDefinition(),
        task_manager=task_manager,
        execution_id=task.id,
        topic="Test Topic",
        user_id=None,
    )

    final_task = await task_manager.get(task.id)
    assert final_task.status == TaskStatus.FAILED


@pytest.mark.asyncio
async def test_run_production_in_background_marks_task_failed_on_unexpected_exception():
    task_manager = BackgroundTaskManager(InMemoryTaskBackend())
    task = await task_manager.submit("youtube_production_run", {"topic": "Test"})
    engine = FakeWorkflowEngine(raises=RuntimeError("boom"))

    # Must never propagate — this runs detached from any request/response cycle.
    await _run_production_in_background(
        workflow_engine=engine,
        workflow_definition=FakeWorkflowDefinition(),
        task_manager=task_manager,
        execution_id=task.id,
        topic="Test Topic",
        user_id=None,
    )

    final_task = await task_manager.get(task.id)
    assert final_task.status == TaskStatus.FAILED


@pytest.mark.asyncio
async def test_run_production_in_background_marks_task_started_before_execution():
    task_manager = BackgroundTaskManager(InMemoryTaskBackend())
    task = await task_manager.submit("youtube_production_run", {"topic": "Test"})
    assert task.status == TaskStatus.PENDING
    engine = FakeWorkflowEngine(final_status="success")

    await _run_production_in_background(
        workflow_engine=engine,
        workflow_definition=FakeWorkflowDefinition(),
        task_manager=task_manager,
        execution_id=task.id,
        topic="Test Topic",
        user_id=None,
    )

    final_task = await task_manager.get(task.id)
    assert final_task.started_at is not None
