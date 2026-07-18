from __future__ import annotations

import abc
from datetime import datetime
from typing import Any

from backend.core.task_models import BackgroundTask, TaskStatus


class TaskBackend(abc.ABC):
    """Protocol for pluggable background task backends."""

    @abc.abstractmethod
    async def submit_task(self, task_type: str, payload: dict[str, Any], delay_seconds: int = 0) -> BackgroundTask:
        raise NotImplementedError

    @abc.abstractmethod
    async def schedule_task(self, task_type: str, payload: dict[str, Any], scheduled_at: datetime) -> BackgroundTask:
        raise NotImplementedError

    @abc.abstractmethod
    async def mark_started(self, task_id: str) -> BackgroundTask:
        raise NotImplementedError

    @abc.abstractmethod
    async def mark_finished(self, task_id: str, succeeded: bool) -> BackgroundTask:
        raise NotImplementedError

    @abc.abstractmethod
    async def get_task(self, task_id: str) -> BackgroundTask | None:
        raise NotImplementedError

    @abc.abstractmethod
    async def list_tasks(self) -> list[BackgroundTask]:
        raise NotImplementedError
