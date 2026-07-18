from __future__ import annotations

import abc
import asyncio
import uuid
from datetime import datetime
from typing import Any

from backend.core.domain_exceptions import ResourceNotFoundError
from backend.core.knowledge_models import KnowledgeChunk, KnowledgeDocument, KnowledgeSource


class KnowledgeRepository(abc.ABC):
    """Abstract interface for knowledge document storage."""

    @abc.abstractmethod
    async def create_document(
        self,
        title: str,
        content: str,
        source: KnowledgeSource,
        metadata: dict[str, Any] | None = None,
    ) -> KnowledgeDocument:
        """Create a new knowledge document."""
        raise NotImplementedError

    @abc.abstractmethod
    async def get_document(self, document_id: str) -> KnowledgeDocument:
        """Retrieve a document by ID."""
        raise NotImplementedError

    @abc.abstractmethod
    async def update_document(
        self,
        document_id: str,
        title: str | None = None,
        content: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> KnowledgeDocument:
        """Update an existing document."""
        raise NotImplementedError

    @abc.abstractmethod
    async def delete_document(self, document_id: str) -> None:
        """Delete a document."""
        raise NotImplementedError

    @abc.abstractmethod
    async def list_documents(
        self,
        source_type: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> tuple[list[KnowledgeDocument], int]:
        """List documents with optional filtering."""
        raise NotImplementedError

    @abc.abstractmethod
    async def create_chunk(
        self,
        document_id: str,
        content: str,
        chunk_index: int,
        metadata: dict[str, Any] | None = None,
    ) -> KnowledgeChunk:
        """Create a chunk within a document."""
        raise NotImplementedError

    @abc.abstractmethod
    async def get_chunks(self, document_id: str) -> list[KnowledgeChunk]:
        """Get all chunks for a document."""
        raise NotImplementedError


class InMemoryKnowledgeRepository(KnowledgeRepository):
    """In-memory knowledge repository for development and foundational use."""

    def __init__(self) -> None:
        self._documents: dict[str, KnowledgeDocument] = {}
        self._chunks: dict[str, list[KnowledgeChunk]] = {}
        self._lock = asyncio.Lock()

    async def create_document(
        self,
        title: str,
        content: str,
        source: KnowledgeSource,
        metadata: dict[str, Any] | None = None,
    ) -> KnowledgeDocument:
        async with self._lock:
            document_id = str(uuid.uuid4())
            now = datetime.utcnow()
            document = KnowledgeDocument(
                id=document_id,
                title=title,
                content=content,
                source=source,
                metadata=metadata or {},
                created_at=now,
                updated_at=now,
            )
            self._documents[document_id] = document
            self._chunks[document_id] = []
            return document

    async def get_document(self, document_id: str) -> KnowledgeDocument:
        if document_id not in self._documents:
            raise ResourceNotFoundError(f"Knowledge document not found: {document_id}")
        document = self._documents[document_id]
        chunks = self._chunks.get(document_id, [])
        return KnowledgeDocument(
            id=document.id,
            title=document.title,
            content=document.content,
            source=document.source,
            chunks=chunks,
            metadata=document.metadata,
            created_at=document.created_at,
            updated_at=document.updated_at,
        )

    async def update_document(
        self,
        document_id: str,
        title: str | None = None,
        content: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> KnowledgeDocument:
        async with self._lock:
            existing = self._documents.get(document_id)
            if existing is None:
                raise ResourceNotFoundError(f"Knowledge document not found: {document_id}")

            updated_document = KnowledgeDocument(
                id=existing.id,
                title=title if title is not None else existing.title,
                content=content if content is not None else existing.content,
                source=existing.source,
                metadata=metadata if metadata is not None else existing.metadata,
                created_at=existing.created_at,
                updated_at=datetime.utcnow(),
            )
            self._documents[document_id] = updated_document
            chunks = self._chunks.get(document_id, [])
            return KnowledgeDocument(
                id=updated_document.id,
                title=updated_document.title,
                content=updated_document.content,
                source=updated_document.source,
                chunks=chunks,
                metadata=updated_document.metadata,
                created_at=updated_document.created_at,
                updated_at=updated_document.updated_at,
            )

    async def delete_document(self, document_id: str) -> None:
        async with self._lock:
            if document_id not in self._documents:
                raise ResourceNotFoundError(f"Knowledge document not found: {document_id}")
            del self._documents[document_id]
            if document_id in self._chunks:
                del self._chunks[document_id]

    async def list_documents(
        self,
        source_type: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> tuple[list[KnowledgeDocument], int]:
        async with self._lock:
            documents = list(self._documents.values())

        def matches(doc: KnowledgeDocument) -> bool:
            if source_type is not None and doc.source.type.value != source_type:
                return False
            return True

        filtered = [doc for doc in documents if matches(doc)]
        total_count = len(filtered)

        offset_val = offset or 0
        if offset_val < 0:
            offset_val = 0

        if limit is not None:
            filtered = filtered[offset_val : offset_val + limit]
        else:
            filtered = filtered[offset_val:]

        # Enrich with chunks
        enriched = []
        for doc in filtered:
            chunks = self._chunks.get(doc.id, [])
            enriched.append(
                KnowledgeDocument(
                    id=doc.id,
                    title=doc.title,
                    content=doc.content,
                    source=doc.source,
                    chunks=chunks,
                    metadata=doc.metadata,
                    created_at=doc.created_at,
                    updated_at=doc.updated_at,
                )
            )

        return enriched, total_count

    async def create_chunk(
        self,
        document_id: str,
        content: str,
        chunk_index: int,
        metadata: dict[str, Any] | None = None,
    ) -> KnowledgeChunk:
        async with self._lock:
            if document_id not in self._documents:
                raise ResourceNotFoundError(f"Knowledge document not found: {document_id}")

            doc = self._documents[document_id]
            chunk_id = str(uuid.uuid4())
            chunk = KnowledgeChunk(
                id=chunk_id,
                document_id=document_id,
                content=content,
                chunk_index=chunk_index,
                source=doc.source,
                metadata=metadata or {},
                created_at=datetime.utcnow(),
            )
            if document_id not in self._chunks:
                self._chunks[document_id] = []
            self._chunks[document_id].append(chunk)
            return chunk

    async def get_chunks(self, document_id: str) -> list[KnowledgeChunk]:
        if document_id not in self._documents:
            raise ResourceNotFoundError(f"Knowledge document not found: {document_id}")
        return self._chunks.get(document_id, [])
