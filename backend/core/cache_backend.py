from __future__ import annotations

import abc
from typing import Any

from backend.core.cache_serializer import CacheSerializer


class CacheBackend(abc.ABC):
    """Abstract cache backend interface."""

    @abc.abstractmethod
    async def get(self, key: str) -> Any | None:
        raise NotImplementedError

    @abc.abstractmethod
    async def set(self, key: str, value: Any, ttl_seconds: int | None = None) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    async def delete(self, key: str) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    async def exists(self, key: str) -> bool:
        raise NotImplementedError

    @abc.abstractmethod
    async def clear(self) -> None:
        raise NotImplementedError
