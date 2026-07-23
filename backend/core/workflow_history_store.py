from __future__ import annotations

import abc
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class WorkflowHistoryRecord:
    """One recorded workflow execution — the basis of a future Workflow History UI."""

    execution_id: str
    workflow_id: str
    topic: str
    status: str  # "running" | "success" | "failed"
    started_at: datetime
    completed_at: datetime | None = None
    steps_executed: list[str] = field(default_factory=list)
    artifacts_generated: list[str] = field(default_factory=list)
    failed_step: str | None = None
    output_folder: str | None = None


class WorkflowHistoryStore(abc.ABC):
    """Abstract interface for workflow execution history storage."""

    @abc.abstractmethod
    async def record_started(self, execution_id: str, workflow_id: str, topic: str) -> WorkflowHistoryRecord:
        raise NotImplementedError

    @abc.abstractmethod
    async def record_step_executed(self, execution_id: str, step_name: str) -> WorkflowHistoryRecord:
        raise NotImplementedError

    @abc.abstractmethod
    async def record_failed(self, execution_id: str, failed_step: str) -> WorkflowHistoryRecord:
        raise NotImplementedError

    @abc.abstractmethod
    async def record_completed(
        self, execution_id: str, artifacts_generated: list[str], output_folder: str
    ) -> WorkflowHistoryRecord:
        raise NotImplementedError

    @abc.abstractmethod
    async def get(self, execution_id: str) -> WorkflowHistoryRecord | None:
        raise NotImplementedError

    @abc.abstractmethod
    async def list_all(self) -> list[WorkflowHistoryRecord]:
        raise NotImplementedError


class InMemoryWorkflowHistoryStore(WorkflowHistoryStore):
    """In-memory workflow history store, mirroring `InMemoryConversationStore`'s pattern."""

    def __init__(self) -> None:
        self._records: dict[str, WorkflowHistoryRecord] = {}

    async def record_started(self, execution_id: str, workflow_id: str, topic: str) -> WorkflowHistoryRecord:
        record = WorkflowHistoryRecord(
            execution_id=execution_id,
            workflow_id=workflow_id,
            topic=topic,
            status="running",
            started_at=datetime.utcnow(),
        )
        self._records[execution_id] = record
        return record

    async def record_step_executed(self, execution_id: str, step_name: str) -> WorkflowHistoryRecord:
        record = self._records[execution_id]
        record.steps_executed.append(step_name)
        return record

    async def record_failed(self, execution_id: str, failed_step: str) -> WorkflowHistoryRecord:
        record = self._records[execution_id]
        record.status = "failed"
        record.failed_step = failed_step
        record.completed_at = datetime.utcnow()
        return record

    async def record_completed(
        self, execution_id: str, artifacts_generated: list[str], output_folder: str
    ) -> WorkflowHistoryRecord:
        record = self._records[execution_id]
        record.status = "success"
        record.artifacts_generated = artifacts_generated
        record.output_folder = output_folder
        record.completed_at = datetime.utcnow()
        return record

    async def get(self, execution_id: str) -> WorkflowHistoryRecord | None:
        return self._records.get(execution_id)

    async def list_all(self) -> list[WorkflowHistoryRecord]:
        return list(self._records.values())
