from __future__ import annotations

import abc
import asyncio
import uuid
from datetime import datetime
from typing import cast

from backend.core.domain_exceptions import ResourceNotFoundError
from backend.core.memory_models import MemoryMetadata, MemoryQuery, MemoryRecord, MemoryResult


class MemoryStore(abc.ABC):
    """Abstract interface for memory storage implementations."""

    @abc.abstractmethod
    async def create_memory(
        self,
        record_type: str,
        content: str,
        metadata: MemoryMetadata | None = None,
    ) -> MemoryRecord:
        raise NotImplementedError

    @abc.abstractmethod
    async def get_memory(self, memory_id: str) -> MemoryRecord:
        raise NotImplementedError

    @abc.abstractmethod
    async def update_memory(
        self,
        memory_id: str,
        content: str | None = None,
        metadata: MemoryMetadata | None = None,
    ) -> MemoryRecord:
        raise NotImplementedError

    @abc.abstractmethod
    async def delete_memory(self, memory_id: str) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    async def query_memory(self, query: MemoryQuery) -> MemoryResult:
        raise NotImplementedError

    @abc.abstractmethod
    async def list_memory(self, limit: int = 20, offset: int = 0) -> MemoryResult:
        raise NotImplementedError


class InMemoryMemoryStore(MemoryStore):
    """In-memory memory store for development and foundational use."""

    def __init__(self) -> None:
        self._memories: dict[str, MemoryRecord] = {}
        self._lock = asyncio.Lock()

    async def create_memory(
        self,
        record_type: str,
        content: str,
        metadata: MemoryMetadata | None = None,
    ) -> MemoryRecord:
        async with self._lock:
            memory_id = str(uuid.uuid4())
            now = datetime.utcnow()
            memory = MemoryRecord(
                id=memory_id,
                record_type=record_type,
                content=content,
                metadata=metadata or MemoryMetadata(),
                created_at=now,
                updated_at=now,
            )
            self._memories[memory_id] = memory
            return memory

    async def get_memory(self, memory_id: str) -> MemoryRecord:
        if memory_id not in self._memories:
            raise ResourceNotFoundError(f"Memory record not found: {memory_id}")
        return self._memories[memory_id]

    async def update_memory(
        self,
        memory_id: str,
        content: str | None = None,
        metadata: MemoryMetadata | None = None,
    ) -> MemoryRecord:
        async with self._lock:
            existing = self._memories.get(memory_id)
            if existing is None:
                raise ResourceNotFoundError(f"Memory record not found: {memory_id}")

            updated_metadata = metadata if metadata is not None else existing.metadata
            updated_content = content if content is not None else existing.content
            updated_memory = MemoryRecord(
                id=existing.id,
                record_type=existing.record_type,
                content=updated_content,
                metadata=updated_metadata,
                created_at=existing.created_at,
                updated_at=datetime.utcnow(),
            )
            self._memories[memory_id] = updated_memory
            return updated_memory

    async def delete_memory(self, memory_id: str) -> None:
        async with self._lock:
            if memory_id not in self._memories:
                raise ResourceNotFoundError(f"Memory record not found: {memory_id}")
            del self._memories[memory_id]

    async def query_memory(self, query: MemoryQuery) -> MemoryResult:
        async with self._lock:
            records = list(self._memories.values())

        def matches(metadata: MemoryMetadata, record: MemoryRecord) -> bool:
            if query.record_type is not None and record.record_type != query.record_type:
                return False
            if query.source is not None and metadata.source != query.source:
                return False
            if query.tags is not None and not set(query.tags).issubset(set(metadata.tags)):
                return False
            if query.metadata_filters is not None:
                for key, value in query.metadata_filters.items():
                    if metadata.attributes.get(key) != value:
                        return False
            if query.created_after is not None and record.created_at <= query.created_after:
                return False
            if query.updated_after is not None and record.updated_at <= query.updated_after:
                return False
            return True

        filtered = [record for record in records if matches(record.metadata, record)]
        total_count = len(filtered)

        offset = query.offset or 0
        if offset < 0:
            offset = 0

        if query.limit is not None:
            filtered = filtered[offset : offset + query.limit]
        else:
            filtered = filtered[offset:]

        return MemoryResult(records=filtered, total_count=total_count)

    async def list_memory(self, limit: int = 20, offset: int = 0) -> MemoryResult:
        async with self._lock:
            records = list(self._memories.values())

        # Order by created_at DESC (newest first)
        records.sort(key=lambda r: r.created_at, reverse=True)
        total_count = len(records)

        offset = max(0, offset)
        paginated = records[offset : offset + limit]

        return MemoryResult(records=paginated, total_count=total_count)
