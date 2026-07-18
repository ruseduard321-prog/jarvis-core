from __future__ import annotations

from typing import Any

from backend.core.event_bus_service import EventBusService
from backend.core.memory_models import MemoryMetadata, MemoryQuery, MemoryRecord, MemoryResult
from backend.core.memory_store import MemoryStore


class MemoryService:
    """Service layer for memory storage and event emission."""

    def __init__(self, store: MemoryStore, event_bus_service: EventBusService) -> None:
        self._store = store
        self._event_bus_service = event_bus_service

    async def create_memory(
        self,
        record_type: str,
        content: str,
        metadata: MemoryMetadata | None = None,
    ) -> MemoryRecord:
        record = await self._store.create_memory(record_type, content, metadata)
        await self._event_bus_service.publish_event(
            "MemoryCreated",
            payload=self._serialize_record(record),
            metadata={"memory_id": record.id},
        )
        return record

    async def get_memory(self, memory_id: str) -> MemoryRecord:
        return await self._store.get_memory(memory_id)

    async def update_memory(
        self,
        memory_id: str,
        content: str | None = None,
        metadata: MemoryMetadata | None = None,
    ) -> MemoryRecord:
        record = await self._store.update_memory(memory_id, content, metadata)
        await self._event_bus_service.publish_event(
            "MemoryUpdated",
            payload=self._serialize_record(record),
            metadata={"memory_id": record.id},
        )
        return record

    async def delete_memory(self, memory_id: str) -> None:
        await self._store.delete_memory(memory_id)
        await self._event_bus_service.publish_event(
            "MemoryDeleted",
            payload={"id": memory_id},
            metadata={"memory_id": memory_id},
        )

    async def query_memory(self, query: MemoryQuery) -> MemoryResult:
        return await self._store.query_memory(query)

    def _serialize_record(self, record: MemoryRecord) -> dict[str, Any]:
        return {
            "id": record.id,
            "record_type": record.record_type,
            "content": record.content,
            "metadata": {
                "source": record.metadata.source,
                "tags": record.metadata.tags,
                "attributes": record.metadata.attributes,
            },
            "created_at": record.created_at.isoformat(),
            "updated_at": record.updated_at.isoformat(),
        }
