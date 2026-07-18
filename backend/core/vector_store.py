from __future__ import annotations

import abc
import asyncio
import uuid
from datetime import datetime
from typing import cast

from backend.core.domain_exceptions import ResourceNotFoundError
from backend.core.vector_models import VectorMetadata, VectorQuery, VectorRecord, VectorSearchResult


class VectorStore(abc.ABC):
    """Abstract interface for vector storage implementations."""

    @abc.abstractmethod
    async def insert_vector(
        self,
        vector: list[float],
        metadata: VectorMetadata | None = None,
    ) -> VectorRecord:
        """Insert a new vector with optional metadata."""
        raise NotImplementedError

    @abc.abstractmethod
    async def get_vector(self, vector_id: str) -> VectorRecord:
        """Retrieve a vector by ID."""
        raise NotImplementedError

    @abc.abstractmethod
    async def update_vector(
        self,
        vector_id: str,
        vector: list[float] | None = None,
        metadata: VectorMetadata | None = None,
    ) -> VectorRecord:
        """Update a vector's content and/or metadata."""
        raise NotImplementedError

    @abc.abstractmethod
    async def delete_vector(self, vector_id: str) -> None:
        """Delete a vector by ID."""
        raise NotImplementedError

    @abc.abstractmethod
    async def list_vectors(self, query: VectorQuery) -> VectorSearchResult:
        """List vectors matching query criteria (not similarity search)."""
        raise NotImplementedError


class InMemoryVectorStore(VectorStore):
    """In-memory vector store for development and foundational use."""

    def __init__(self) -> None:
        self._vectors: dict[str, VectorRecord] = {}
        self._lock = asyncio.Lock()

    async def insert_vector(
        self,
        vector: list[float],
        metadata: VectorMetadata | None = None,
    ) -> VectorRecord:
        async with self._lock:
            vector_id = str(uuid.uuid4())
            now = datetime.utcnow()
            record = VectorRecord(
                id=vector_id,
                vector=vector,
                metadata=metadata or VectorMetadata(),
                created_at=now,
                updated_at=now,
            )
            self._vectors[vector_id] = record
            return record

    async def get_vector(self, vector_id: str) -> VectorRecord:
        if vector_id not in self._vectors:
            raise ResourceNotFoundError(f"Vector record not found: {vector_id}")
        return self._vectors[vector_id]

    async def update_vector(
        self,
        vector_id: str,
        vector: list[float] | None = None,
        metadata: VectorMetadata | None = None,
    ) -> VectorRecord:
        async with self._lock:
            existing = self._vectors.get(vector_id)
            if existing is None:
                raise ResourceNotFoundError(f"Vector record not found: {vector_id}")

            updated_vector = vector if vector is not None else existing.vector
            updated_metadata = metadata if metadata is not None else existing.metadata
            updated_record = VectorRecord(
                id=existing.id,
                vector=updated_vector,
                metadata=updated_metadata,
                created_at=existing.created_at,
                updated_at=datetime.utcnow(),
            )
            self._vectors[vector_id] = updated_record
            return updated_record

    async def delete_vector(self, vector_id: str) -> None:
        async with self._lock:
            if vector_id not in self._vectors:
                raise ResourceNotFoundError(f"Vector record not found: {vector_id}")
            del self._vectors[vector_id]

    async def list_vectors(self, query: VectorQuery) -> VectorSearchResult:
        async with self._lock:
            records = list(self._vectors.values())

        def matches(record: VectorRecord) -> bool:
            metadata = record.metadata
            if query.namespace is not None and metadata.namespace != query.namespace:
                return False
            if query.tags is not None and not set(query.tags).issubset(set(metadata.tags)):
                return False
            if query.metadata_filters is not None:
                for key, value in query.metadata_filters.items():
                    if metadata.attributes.get(key) != value:
                        return False
            return True

        filtered = [record for record in records if matches(record)]
        total_count = len(filtered)

        offset = query.offset or 0
        if offset < 0:
            offset = 0

        if query.limit is not None:
            filtered = filtered[offset : offset + query.limit]
        else:
            filtered = filtered[offset:]

        return VectorSearchResult(records=filtered, total_count=total_count)
