from __future__ import annotations

import abc
from typing import Any, Coroutine, Protocol

from backend.core.event_models import Event


class EventHandler(Protocol):
    def __call__(self, event: Event) -> Any | Coroutine[Any, Any, Any]:
        ...


class EventBus(abc.ABC):
    """Abstract event bus interface."""

    @abc.abstractmethod
    async def publish(self, event: Event) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    async def subscribe(self, event_type: str, handler: EventHandler) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    async def unsubscribe(self, event_type: str, handler: EventHandler) -> None:
        raise NotImplementedError
