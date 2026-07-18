from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
import uuid


@dataclass(frozen=True)
class Event:
    """Domain event envelope."""

    event_id: str
    event_type: str
    timestamp: datetime
    payload: dict[str, Any]
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(cls, event_type: str, payload: dict[str, Any], metadata: dict[str, Any] | None = None) -> "Event":
        return cls(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            timestamp=datetime.utcnow(),
            payload=payload,
            metadata=metadata or {},
        )
