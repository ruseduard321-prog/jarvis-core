from __future__ import annotations

import pytest

from backend.core.provider_exceptions import PermanentProviderError, TransientProviderError
from backend.core.retry import retry_with_backoff


@pytest.mark.asyncio
async def test_retry_succeeds_after_transient_failures(monkeypatch):
    import backend.core.retry as retry_module

    sleeps: list[float] = []

    async def _fake_sleep(seconds: float) -> None:
        sleeps.append(seconds)

    monkeypatch.setattr(retry_module.asyncio, "sleep", _fake_sleep)

    attempts = {"count": 0}

    async def _operation():
        attempts["count"] += 1
        if attempts["count"] < 3:
            raise TransientProviderError("temporary")
        return "ok"

    result = await retry_with_backoff(_operation, max_attempts=5, base_delay_seconds=0.1)

    assert result == "ok"
    assert attempts["count"] == 3
    assert sleeps == [0.1, 0.2]


@pytest.mark.asyncio
async def test_retry_gives_up_after_max_attempts(monkeypatch):
    import backend.core.retry as retry_module

    async def _fake_sleep(seconds: float) -> None:
        return None

    monkeypatch.setattr(retry_module.asyncio, "sleep", _fake_sleep)

    async def _operation():
        raise TransientProviderError("always fails")

    with pytest.raises(TransientProviderError):
        await retry_with_backoff(_operation, max_attempts=3, base_delay_seconds=0.01)


@pytest.mark.asyncio
async def test_retry_does_not_retry_permanent_errors():
    attempts = {"count": 0}

    async def _operation():
        attempts["count"] += 1
        raise PermanentProviderError("not retryable")

    with pytest.raises(PermanentProviderError):
        await retry_with_backoff(_operation, max_attempts=5, base_delay_seconds=0.01)

    assert attempts["count"] == 1


@pytest.mark.asyncio
async def test_retry_on_attempt_fires_once_per_attempt_until_success(monkeypatch):
    import backend.core.retry as retry_module

    async def _fake_sleep(seconds: float) -> None:
        return None

    monkeypatch.setattr(retry_module.asyncio, "sleep", _fake_sleep)

    seen_attempts: list[int] = []
    call_count = {"count": 0}

    async def _operation():
        call_count["count"] += 1
        if call_count["count"] < 3:
            raise TransientProviderError("temporary")
        return "ok"

    result = await retry_with_backoff(
        _operation, max_attempts=5, base_delay_seconds=0.01, on_attempt=seen_attempts.append
    )

    assert result == "ok"
    assert seen_attempts == [1, 2, 3]


@pytest.mark.asyncio
async def test_retry_on_attempt_fires_once_on_immediate_success():
    seen_attempts: list[int] = []

    async def _operation():
        return "ok"

    result = await retry_with_backoff(_operation, on_attempt=seen_attempts.append)

    assert result == "ok"
    assert seen_attempts == [1]


@pytest.mark.asyncio
async def test_retry_on_attempt_fires_before_permanent_error_and_stops():
    seen_attempts: list[int] = []

    async def _operation():
        raise PermanentProviderError("not retryable")

    with pytest.raises(PermanentProviderError):
        await retry_with_backoff(_operation, max_attempts=5, base_delay_seconds=0.01, on_attempt=seen_attempts.append)

    assert seen_attempts == [1]
