from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import Any

from backend.core.event_bus import EventBus, EventHandler
from backend.core.event_models import Event


class InMemoryEventBus(EventBus):
    """In-memory event bus for synchronous and asynchronous handlers."""

    def __init__(self) -> None:
        self._subscribers: dict[str, list[EventHandler]] = defaultdict(list)
        self._lock = asyncio.Lock()

    async def publish(self, event: Event) -> None:
        async with self._lock:
            handlers = list(self._subscribers.get(event.event_type, []))
        for handler in handlers:
            result = handler(event)
            if asyncio.iscoroutine(result):
                await result

    async def subscribe(self, event_type: str, handler: EventHandler) -> None:
        async with self._lock:
            if handler not in self._subscribers[event_type]:
                self._subscribers[event_type].append(handler)

    async def unsubscribe(self, event_type: str, handler: EventHandler) -> None:
        async with self._lock:
            if handler in self._subscribers[event_type]:
                self._subscribers[event_type].remove(handler)
