from __future__ import annotations

from typing import Any

from backend.core.embedding_models import EmbeddingRequest
from backend.core.embedding_provider import EmbeddingProvider
from backend.core.event_bus_service import EventBusService
from backend.core.retrieval_engine import RetrievalEngine
from backend.core.retrieval_models import RetrievalRequest, RetrievalResult, RetrievedDocument
from backend.core.vector_models import VectorQuery
from backend.core.vector_service import VectorService


class RetrievalEngineService(RetrievalEngine):
    """Default retrieval engine implementation."""

    def __init__(
        self,
        embedding_provider: EmbeddingProvider,
        vector_service: VectorService,
        event_bus_service: EventBusService,
    ) -> None:
        self._embedding_provider = embedding_provider
        self._vector_service = vector_service
        self._event_bus_service = event_bus_service

    async def retrieve(self, request: RetrievalRequest) -> RetrievalResult:
        """
        Retrieve documents via embeddings and vector search.

        Pipeline:
        1. Generate embedding for query text
        2. Retrieve vectors from vector store (metadata-based, not similarity)
        3. Return as standardized retrieval result
        """
        # Generate query embedding
        embedding_response = await self._embedding_provider.generate_embeddings(
            EmbeddingRequest(texts=[request.query], options=request.options)
        )

        # Emit event for tracking
        await self._event_bus_service.publish_event(
            "EmbeddingGenerated",
            payload={
                "query": request.query,
                "model": embedding_response.model,
                "embedding_dim": len(embedding_response.embeddings[0]) if embedding_response.embeddings else 0,
            },
            metadata={"query": request.query},
        )

        # List vectors from store (metadata-based filtering only)
        # Note: actual similarity search happens in future vector DB providers
        vector_query = VectorQuery(
            namespace=request.namespace,
            tags=request.tags,
            metadata_filters=request.metadata_filters,
            limit=request.limit or 10,
        )
        vector_result = await self._vector_service.list_vectors(vector_query)

        # Convert vectors to retrieved documents
        documents = [
            RetrievedDocument(
                id=record.id,
                content=record.metadata.attributes.get("content", ""),
                source=record.metadata.source,
                metadata=record.metadata.attributes,
            )
            for record in vector_result.records
        ]

        return RetrievalResult(
            documents=documents,
            total_count=vector_result.total_count,
        )
