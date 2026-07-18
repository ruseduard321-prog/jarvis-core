from __future__ import annotations

import abc
from dataclasses import dataclass
from typing import Any, Callable, AsyncIterator


@dataclass(frozen=True)
class StreamingResponse:
    """A streaming response that can be consumed asynchronously."""

    stream_id: str
    event_type: str
    data: Any
    metadata: dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            object.__setattr__(self, "metadata", {})


class StreamCallback(abc.ABC):
    """Abstract callback for stream events."""

    @abc.abstractmethod
    async def on_data(self, response: StreamingResponse) -> None:
        """Called when data is available."""
        raise NotImplementedError

    @abc.abstractmethod
    async def on_error(self, error: str) -> None:
        """Called when an error occurs."""
        raise NotImplementedError

    @abc.abstractmethod
    async def on_complete(self) -> None:
        """Called when stream is complete."""
        raise NotImplementedError


class StreamingEngine(abc.ABC):
    """Abstract interface for streaming operations."""

    @abc.abstractmethod
    async def stream(
        self,
        source: Any,
        callback: StreamCallback | None = None,
    ) -> AsyncIterator[StreamingResponse]:
        """Stream data with optional callback."""
        raise NotImplementedError

    @abc.abstractmethod
    async def cancel(self, stream_id: str) -> None:
        """Cancel an active stream."""
        raise NotImplementedError
