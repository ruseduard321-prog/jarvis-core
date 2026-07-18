from __future__ import annotations

import pickle
from typing import Any, Protocol


class CacheSerializer(Protocol):
    """Serialization abstraction for cache values."""

    def serialize(self, value: Any) -> bytes:
        raise NotImplementedError

    def deserialize(self, data: bytes) -> Any:
        raise NotImplementedError


class PickleCacheSerializer:
    """Default serializer that supports arbitrary Python objects."""

    def serialize(self, value: Any) -> bytes:
        return pickle.dumps(value)

    def deserialize(self, data: bytes) -> Any:
        return pickle.loads(data)
