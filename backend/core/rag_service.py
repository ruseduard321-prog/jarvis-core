from __future__ import annotations

import abc
from typing import Any

from backend.core.rag_models import RAGContext, RetrievedContext
from backend.core.retrieval_engine import RetrievalEngine
from backend.core.retrieval_models import RetrievalRequest
from backend.core.memory_service import MemoryService
from backend.core.memory_models import MemoryQuery
from backend.core.event_bus_service import EventBusService


class ContextBuilder(abc.ABC):
    """Abstract interface for building retrieval context."""

    @abc.abstractmethod
    async def build(self, rag_context: RAGContext) -> RetrievedContext:
        """Build retrieved context from knowledge sources."""
        raise NotImplementedError


class DefaultContextBuilder(ContextBuilder):
    """Default context builder that retrieves from knowledge base and memory."""

    def __init__(
        self,
        retrieval_engine: RetrievalEngine,
        memory_service: MemoryService,
    ) -> None:
        self._retrieval_engine = retrieval_engine
        self._memory_service = memory_service

    async def build(self, rag_context: RAGContext) -> RetrievedContext:
        """Build context by retrieving from knowledge base and memory."""
        # Retrieve from knowledge base
        retrieval_result = await self._retrieval_engine.retrieve(
            RetrievalRequest(
                query=rag_context.user_query,
                namespace=rag_context.namespace,
                tags=rag_context.tags,
                limit=10,
            )
        )

        # Retrieve from memory
        memory_result = await self._memory_service.query_memory(
            MemoryQuery(
                tags=rag_context.tags,
                limit=5,
            )
        )

        return RetrievedContext(
            documents=[
                {
                    "id": doc.id,
                    "content": doc.content,
                    "source": doc.source,
                }
                for doc in retrieval_result.documents
            ],
            memory_records=[
                {
                    "id": record.id,
                    "content": record.content,
                    "record_type": record.record_type,
                }
                for record in memory_result.records
            ],
            total_retrieved=retrieval_result.total_count + memory_result.total_count,
        )


class PromptAugmenter(abc.ABC):
    """Abstract interface for augmenting prompts with context."""

    @abc.abstractmethod
    async def augment(self, rag_context: RAGContext) -> str:
        """Augment prompt with retrieved context."""
        raise NotImplementedError


class DefaultPromptAugmenter(PromptAugmenter):
    """Default prompt augmenter that combines query with retrieved context."""

    async def augment(self, rag_context: RAGContext) -> str:
        """Augment prompt with retrieved context."""
        if not rag_context.retrieved_context:
            return rag_context.user_query

        augmented = f"{rag_context.user_query}\n\n"
        
        if rag_context.retrieved_context.documents:
            augmented += "## Retrieved Documents\n"
            for doc in rag_context.retrieved_context.documents:
                augmented += f"\n- **{doc.get('source', 'Unknown')}**: {doc.get('content', '')}\n"

        if rag_context.retrieved_context.memory_records:
            augmented += "\n## Memory Context\n"
            for record in rag_context.retrieved_context.memory_records:
                augmented += f"\n- **{record.get('record_type', 'Unknown')}**: {record.get('content', '')}\n"

        return augmented


class RAGService:
    """Service orchestrating RAG pipeline: Query → Embedding → Retrieval → Context → Augmentation."""

    def __init__(
        self,
        context_builder: ContextBuilder,
        prompt_augmenter: PromptAugmenter,
        event_bus_service: EventBusService,
    ) -> None:
        self._context_builder = context_builder
        self._prompt_augmenter = prompt_augmenter
        self._event_bus_service = event_bus_service

    async def execute(self, rag_context: RAGContext) -> RAGContext:
        """Execute full RAG pipeline."""
        # Build retrieved context
        retrieved_context = await self._context_builder.build(rag_context)

        # Augment prompt with retrieved context
        augmented_prompt = await self._prompt_augmenter.augment(
            RAGContext(
                user_query=rag_context.user_query,
                namespace=rag_context.namespace,
                tags=rag_context.tags,
                conversation_id=rag_context.conversation_id,
                user_id=rag_context.user_id,
                retrieved_context=retrieved_context,
                metadata=rag_context.metadata,
            )
        )

        result = RAGContext(
            user_query=rag_context.user_query,
            namespace=rag_context.namespace,
            tags=rag_context.tags,
            conversation_id=rag_context.conversation_id,
            user_id=rag_context.user_id,
            retrieved_context=retrieved_context,
            augmented_prompt=augmented_prompt,
            metadata=rag_context.metadata,
        )

        await self._event_bus_service.publish_event(
            "RAGCompleted",
            payload={
                "query": rag_context.user_query,
                "documents_retrieved": retrieved_context.total_retrieved,
            },
            metadata={"user_id": rag_context.user_id},
        )

        return result
