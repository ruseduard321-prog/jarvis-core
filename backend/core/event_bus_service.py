from __future__ import annotations

from typing import Any

from backend.core.event_bus import EventBus
from backend.core.event_models import Event


class EventBusService:
    """Service layer for event bus dispatching."""

    def __init__(self, event_bus: EventBus) -> None:
        self._event_bus = event_bus

    async def publish_event(self, event_type: str, payload: dict[str, Any], metadata: dict[str, Any] | None = None) -> None:
        event = Event.create(event_type=event_type, payload=payload, metadata=metadata)
        await self._event_bus.publish(event)
