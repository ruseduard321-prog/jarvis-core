from __future__ import annotations

from typing import Any

from backend.core.event_bus_service import EventBusService
from backend.core.vector_models import VectorMetadata, VectorQuery, VectorRecord, VectorSearchResult
from backend.core.vector_store import VectorStore


class VectorService:
    """Service layer for vector storage and event emission."""

    def __init__(self, store: VectorStore, event_bus_service: EventBusService) -> None:
        self._store = store
        self._event_bus_service = event_bus_service

    async def insert_vector(
        self,
        vector: list[float],
        metadata: VectorMetadata | None = None,
    ) -> VectorRecord:
        record = await self._store.insert_vector(vector, metadata)
        await self._event_bus_service.publish_event(
            "VectorCreated",
            payload=self._serialize_record(record),
            metadata={"vector_id": record.id},
        )
        return record

    async def get_vector(self, vector_id: str) -> VectorRecord:
        return await self._store.get_vector(vector_id)

    async def update_vector(
        self,
        vector_id: str,
        vector: list[float] | None = None,
        metadata: VectorMetadata | None = None,
    ) -> VectorRecord:
        record = await self._store.update_vector(vector_id, vector, metadata)
        await self._event_bus_service.publish_event(
            "VectorUpdated",
            payload=self._serialize_record(record),
            metadata={"vector_id": record.id},
        )
        return record

    async def delete_vector(self, vector_id: str) -> None:
        await self._store.delete_vector(vector_id)
        await self._event_bus_service.publish_event(
            "VectorDeleted",
            payload={"id": vector_id},
            metadata={"vector_id": vector_id},
        )

    async def list_vectors(self, query: VectorQuery) -> VectorSearchResult:
        return await self._store.list_vectors(query)

    def _serialize_record(self, record: VectorRecord) -> dict[str, Any]:
        return {
            "id": record.id,
            "vector": record.vector,
            "metadata": {
                "source": record.metadata.source,
                "tags": record.metadata.tags,
                "namespace": record.metadata.namespace,
                "attributes": record.metadata.attributes,
            },
            "created_at": record.created_at.isoformat(),
            "updated_at": record.updated_at.isoformat(),
        }
