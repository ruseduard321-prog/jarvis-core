from __future__ import annotations

import asyncio
import logging
from typing import Awaitable, Callable, TypeVar

from backend.core.provider_exceptions import PermanentProviderError, TransientProviderError

logger = logging.getLogger(__name__)
T = TypeVar("T")


async def retry_with_backoff(
    operation: Callable[[], Awaitable[T]],
    *,
    max_attempts: int = 3,
    base_delay_seconds: float = 0.5,
    on_attempt: Callable[[int], None] | None = None,
) -> T:
    """Retry `operation` with exponential backoff. Only `TransientProviderError` is
    retried; `PermanentProviderError` (and anything else) propagates immediately.

    `on_attempt`, when provided, is invoked with the current attempt number (1-based)
    before each try, so callers can capture retry counts via a closure."""
    attempt = 0
    while True:
        attempt += 1
        if on_attempt is not None:
            on_attempt(attempt)
        try:
            return await operation()
        except PermanentProviderError:
            raise
        except TransientProviderError:
            if attempt >= max_attempts:
                raise
            delay = base_delay_seconds * (2 ** (attempt - 1))
            logger.warning("provider_retry", extra={"attempt": attempt, "delay_seconds": delay})
            await asyncio.sleep(delay)
