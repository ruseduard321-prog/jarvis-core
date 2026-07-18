from __future__ import annotations

import asyncio
import time
from typing import Protocol

from starlette.requests import Request


class RateLimitStore(Protocol):
    async def increment(self, key: str, window_seconds: int) -> tuple[int, int]:
        """Increment the request count for the given key.

        Returns:
            A tuple containing the current count and reset timestamp.
        """


class InMemoryRateLimitStore:
    """In-memory rate limit store for backend-agnostic usage."""

    def __init__(self) -> None:
        self._data: dict[str, tuple[int, int]] = {}
        self._lock = asyncio.Lock()

    async def increment(self, key: str, window_seconds: int) -> tuple[int, int]:
        async with self._lock:
            now = int(time.time())
            count, reset_timestamp = self._data.get(key, (0, now + window_seconds))
            if reset_timestamp <= now:
                count = 0
                reset_timestamp = now + window_seconds

            count += 1
            self._data[key] = (count, reset_timestamp)
            return count, reset_timestamp


def get_client_identifier(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()

    client = request.client
    return client.host if client is not None and client.host else "unknown"


def make_rate_limit_key(namespace: str, identifier: str, path: str) -> str:
    return f"{namespace}:{identifier}:{path}"
