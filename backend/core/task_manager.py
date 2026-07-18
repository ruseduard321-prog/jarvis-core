from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Any

from backend.core.task_backend import TaskBackend
from backend.core.task_models import BackgroundTask, TaskStatus


class BackgroundTaskManager:
    """Facade for submitting and tracking background tasks."""

    def __init__(self, backend: TaskBackend) -> None:
        self.backend = backend

    async def submit(self, task_type: str, payload: dict[str, Any], delay_seconds: int = 0) -> BackgroundTask:
        return await self.backend.submit_task(task_type, payload, delay_seconds=delay_seconds)

    async def schedule(self, task_type: str, payload: dict[str, Any], delay_seconds: int = 0) -> BackgroundTask:
        scheduled_at = datetime.utcnow() + timedelta(seconds=delay_seconds)
        return await self.backend.schedule_task(task_type, payload, scheduled_at=scheduled_at)

    async def mark_started(self, task_id: str) -> BackgroundTask:
        return await self.backend.mark_started(task_id)

    async def mark_finished(self, task_id: str, succeeded: bool) -> BackgroundTask:
        return await self.backend.mark_finished(task_id, succeeded)

    async def get(self, task_id: str) -> BackgroundTask | None:
        return await self.backend.get_task(task_id)

    async def list(self) -> list[BackgroundTask]:
        return await self.backend.list_tasks()


class InMemoryTaskBackend(TaskBackend):
    def __init__(self) -> None:
        self._tasks: dict[str, BackgroundTask] = {}
        self._lock = asyncio.Lock()

    async def submit_task(self, task_type: str, payload: dict[str, Any], delay_seconds: int = 0) -> BackgroundTask:
        async with self._lock:
            task_id = str(uuid.uuid4())
            task = BackgroundTask(
                id=task_id,
                task_type=task_type,
                payload=payload,
                status=TaskStatus.SCHEDULED if delay_seconds > 0 else TaskStatus.PENDING,
                created_at=datetime.utcnow(),
                delay_seconds=delay_seconds,
                scheduled_at=(datetime.utcnow() + timedelta(seconds=delay_seconds)) if delay_seconds > 0 else None,
            )
            self._tasks[task_id] = task
            return task

    async def schedule_task(self, task_type: str, payload: dict[str, Any], scheduled_at: datetime) -> BackgroundTask:
        async with self._lock:
            task_id = str(uuid.uuid4())
            task = BackgroundTask(
                id=task_id,
                task_type=task_type,
                payload=payload,
                status=TaskStatus.SCHEDULED,
                created_at=datetime.utcnow(),
                scheduled_at=scheduled_at,
            )
            self._tasks[task_id] = task
            return task

    async def mark_started(self, task_id: str) -> BackgroundTask:
        async with self._lock:
            task = self._tasks[task_id]
            updated = BackgroundTask(
                **{
                    **task.as_dict(),
                    "status": TaskStatus.RUNNING,
                    "started_at": datetime.utcnow().isoformat(),
                }
            )
            updated = BackgroundTask(
                id=task.id,
                task_type=task.task_type,
                payload=task.payload,
                status=TaskStatus.RUNNING,
                created_at=task.created_at,
                started_at=datetime.utcnow(),
                finished_at=task.finished_at,
                retry_count=task.retry_count,
                delay_seconds=task.delay_seconds,
                scheduled_at=task.scheduled_at,
            )
            self._tasks[task_id] = updated
            return updated

    async def mark_finished(self, task_id: str, succeeded: bool) -> BackgroundTask:
        async with self._lock:
            task = self._tasks[task_id]
            status = TaskStatus.SUCCEEDED if succeeded else TaskStatus.FAILED
            updated = BackgroundTask(
                id=task.id,
                task_type=task.task_type,
                payload=task.payload,
                status=status,
                created_at=task.created_at,
                started_at=task.started_at,
                finished_at=datetime.utcnow(),
                retry_count=task.retry_count + (0 if succeeded else 1),
                delay_seconds=task.delay_seconds,
                scheduled_at=task.scheduled_at,
            )
            self._tasks[task_id] = updated
            return updated

    async def get_task(self, task_id: str) -> BackgroundTask | None:
        return self._tasks.get(task_id)

    async def list_tasks(self) -> list[BackgroundTask]:
        return list(self._tasks.values())
