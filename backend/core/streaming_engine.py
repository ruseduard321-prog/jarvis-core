from __future__ import annotations

import uuid
from typing import Any, AsyncIterator

from backend.core.streaming_models import StreamCallback, StreamingEngine, StreamingResponse


class DefaultStreamingEngine(StreamingEngine):
    """Default streaming engine for handling stream sources."""

    def __init__(self) -> None:
        self._active_streams: dict[str, bool] = {}

    async def stream(
        self,
        source: Any,
        callback: StreamCallback | None = None,
    ) -> AsyncIterator[StreamingResponse]:
        """Stream data from source with optional callback."""
        stream_id = str(uuid.uuid4())
        self._active_streams[stream_id] = True

        try:
            # If source is an async iterator, consume it
            if hasattr(source, "__aiter__"):
                index = 0
                async for item in source:
                    if not self._active_streams.get(stream_id, False):
                        break

                    response = StreamingResponse(
                        stream_id=stream_id,
                        event_type="data",
                        data=item,
                        metadata={"index": index},
                    )

                    if callback:
                        await callback.on_data(response)

                    yield response
                    index += 1

            if callback:
                await callback.on_complete()

        except Exception as e:
            if callback:
                await callback.on_error(str(e))
            raise
        finally:
            self._active_streams.pop(stream_id, None)

    async def cancel(self, stream_id: str) -> None:
        """Cancel an active stream."""
        self._active_streams[stream_id] = False
