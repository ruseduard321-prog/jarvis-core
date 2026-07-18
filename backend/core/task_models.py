from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class TaskStatus(str, Enum):
    """Task lifecycle status values."""

    PENDING = "pending"
    SCHEDULED = "scheduled"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


@dataclass(frozen=True)
class BackgroundTask:
    """Representation of a background task."""

    id: str
    task_type: str
    payload: dict[str, Any]
    status: TaskStatus
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None
    retry_count: int = 0
    delay_seconds: int = 0
    scheduled_at: datetime | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "task_type": self.task_type,
            "payload": self.payload,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
            "retry_count": self.retry_count,
            "delay_seconds": self.delay_seconds,
            "scheduled_at": self.scheduled_at.isoformat() if self.scheduled_at else None,
        }
