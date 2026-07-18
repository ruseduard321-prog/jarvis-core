from __future__ import annotations

import asyncio
import time
from typing import Any

from backend.core.cache_backend import CacheBackend
from backend.core.cache_serializer import CacheSerializer, PickleCacheSerializer


class CacheManager:
    """Facade for using a cache backend with optional key namespacing."""

    def __init__(self, backend: CacheBackend, namespace: str = "default", serializer: CacheSerializer | None = None) -> None:
        self.backend = backend
        self.namespace = namespace
        self.serializer = serializer or PickleCacheSerializer()

    def _namespaced_key(self, key: str) -> str:
        return f"{self.namespace}:{key}"

    async def get(self, key: str) -> Any | None:
        namespaced_key = self._namespaced_key(key)
        raw = await self.backend.get(namespaced_key)
        if raw is None:
            return None
        return self.serializer.deserialize(raw)

    async def set(self, key: str, value: Any, ttl_seconds: int | None = None) -> None:
        namespaced_key = self._namespaced_key(key)
        raw = self.serializer.serialize(value)
        await self.backend.set(namespaced_key, raw, ttl_seconds=ttl_seconds)

    async def delete(self, key: str) -> None:
        namespaced_key = self._namespaced_key(key)
        await self.backend.delete(namespaced_key)

    async def exists(self, key: str) -> bool:
        namespaced_key = self._namespaced_key(key)
        return await self.backend.exists(namespaced_key)

    async def clear(self) -> None:
        await self.backend.clear()


class InMemoryCacheBackend(CacheBackend):
    def __init__(self) -> None:
        self._store: dict[str, tuple[bytes, int | None]] = {}
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Any | None:
        async with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return None
            value, expires_at = entry
            if expires_at is not None and expires_at <= time.time():
                del self._store[key]
                return None
            return value

    async def set(self, key: str, value: Any, ttl_seconds: int | None = None) -> None:
        expires_at = time.time() + ttl_seconds if ttl_seconds is not None else None
        async with self._lock:
            self._store[key] = (value, expires_at)

    async def delete(self, key: str) -> None:
        async with self._lock:
            self._store.pop(key, None)

    async def exists(self, key: str) -> bool:
        async with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return False
            _, expires_at = entry
            if expires_at is not None and expires_at <= time.time():
                del self._store[key]
                return False
            return True

    async def clear(self) -> None:
        async with self._lock:
            self._store.clear()
