from __future__ import annotations

from typing import Callable, TypeVar

from backend.auth.auth_service import AuthService
from backend.auth.supabase_auth import SupabaseAuthClient
from backend.core.cache_manager import CacheManager, InMemoryCacheBackend
from backend.core.config import Settings, settings
from backend.core.database import DatabaseProvider
from backend.core.event_bus import EventBus
from backend.core.event_bus_service import EventBusService
from backend.core.in_memory_event_bus import InMemoryEventBus
from backend.core.llm_provider import LLMProvider
from backend.core.llm_provider_registry import LLMProviderRegistry
from backend.core.llm_registry import llm_provider_registry
from backend.core.metrics import InMemoryMetricsProvider, MetricsProvider
from backend.core.openai_llm_provider import OpenAIProvider
from backend.core.prompt_registry import PromptRegistry
from backend.core.prompt_registry_provider import prompt_registry
from backend.core.prompt_template_service import PromptTemplateService
from backend.core.conversation_engine import ConversationEngine
from backend.core.conversation_engine_service import ConversationEngineService
from backend.core.conversation_store import ConversationStore
from backend.core.conversation_store_provider import conversation_store
from backend.core.memory_service import MemoryService
from backend.core.memory_store import InMemoryMemoryStore, MemoryStore
from backend.core.memory_store_provider import memory_store
from backend.core.vector_service import VectorService
from backend.core.vector_store import InMemoryVectorStore, VectorStore
from backend.core.vector_store_provider import vector_store
from backend.core.embedding_provider import EmbeddingProvider
from backend.core.embedding_provider_registry import EmbeddingProviderRegistry
from backend.core.embedding_registry_provider import embedding_provider_registry
from backend.core.retrieval_engine import RetrievalEngine
from backend.core.retrieval_engine_service import RetrievalEngineService
from backend.core.knowledge_repository import KnowledgeRepository
from backend.core.knowledge_repository_provider import knowledge_repository
from backend.core.tool import Tool, ToolRegistry
from backend.core.tool_registry_provider import tool_registry
from backend.core.tool_executor import ToolExecutor
from backend.core.agent import Agent, AgentRegistry
from backend.core.agent_registry_provider import agent_registry
from backend.core.agent_runtime import AgentRuntime
from backend.core.rag_service import RAGService, ContextBuilder, DefaultContextBuilder, PromptAugmenter, DefaultPromptAugmenter
from backend.core.streaming_engine import DefaultStreamingEngine
from backend.core.streaming_models import StreamingEngine
from backend.core.ai_orchestrator import AIOrchestrator
from backend.core.ai_orchestrator_service import AIOrchestratorService
from backend.core.service_registry import service_registry
from backend.core.supabase_provider import SupabaseProvider
from backend.core.task_manager import BackgroundTaskManager, InMemoryTaskBackend
from backend.core.document_ingestion import DocumentIngestionEngine

T = TypeVar("T")


def register_singleton(service_type: type[T], factory: Callable[[], T]) -> None:
    """Register a lazy singleton service in the central registry."""
    service_registry.register_singleton(service_type, factory)


def register_instance(service_type: type[T], instance: T) -> None:
    """Register an existing singleton instance."""
    service_registry.register_instance(service_type, instance)


def override_singleton(service_type: type[T], factory: Callable[[], T]) -> None:
    """Replace the service factory for a registered service."""
    service_registry.override_singleton(service_type, factory)


def get_settings() -> Settings:
    """Return the application settings singleton."""
    return service_registry.get(Settings)


def get_database() -> DatabaseProvider:
    """Return the singleton database provider instance."""
    return service_registry.get(DatabaseProvider)


def get_event_bus() -> EventBus:
    """Return the shared event bus instance."""
    return service_registry.get(EventBus)


def get_event_bus_service() -> EventBusService:
    """Return the shared event bus service façade."""
    return service_registry.get(EventBusService)


def get_cache_manager() -> CacheManager:
    """Return the shared cache manager instance."""
    return service_registry.get(CacheManager)


def get_task_manager() -> BackgroundTaskManager:
    """Return the shared background task manager instance."""
    return service_registry.get(BackgroundTaskManager)


def get_metrics_provider() -> MetricsProvider:
    """Return the shared metrics provider instance."""
    return service_registry.get(MetricsProvider)


def get_supabase_auth_client() -> SupabaseAuthClient:
    """Return the configured Supabase auth client instance."""
    return service_registry.get(SupabaseAuthClient)


def get_auth_service() -> AuthService:
    """Return the shared authentication service instance."""
    return service_registry.get(AuthService)


def get_llm_provider(provider_name: str | None = None) -> LLMProvider:
    """Return the selected LLM provider instance."""
    if provider_name is None:
        return service_registry.get(LLMProvider)
    return llm_provider_registry.get(provider_name)


def get_llm_provider_registry() -> LLMProviderRegistry:
    """Return the shared LLM provider registry."""
    return service_registry.get(LLMProviderRegistry)


def get_prompt_registry() -> PromptRegistry:
    """Return the shared prompt template registry."""
    return service_registry.get(PromptRegistry)


def get_prompt_template_service() -> PromptTemplateService:
    """Return the shared prompt template service."""
    return service_registry.get(PromptTemplateService)


def get_ai_orchestrator() -> AIOrchestrator:
    """Return the shared AI orchestrator instance."""
    return service_registry.get(AIOrchestrator)


def get_conversation_engine() -> ConversationEngine:
    """Return the shared conversation engine instance."""
    return service_registry.get(ConversationEngine)


def get_conversation_store() -> ConversationStore:
    """Return the shared conversation store instance."""
    return service_registry.get(ConversationStore)


def get_memory_store() -> MemoryStore:
    """Return the shared memory store instance."""
    return service_registry.get(MemoryStore)


def get_memory_service() -> MemoryService:
    """Return the shared memory service instance."""
    return service_registry.get(MemoryService)


def get_vector_store() -> VectorStore:
    """Return the shared vector store instance."""
    return service_registry.get(VectorStore)


def get_vector_service() -> VectorService:
    """Return the shared vector service instance."""
    return service_registry.get(VectorService)


def get_embedding_provider_registry() -> EmbeddingProviderRegistry:
    """Return the shared embedding provider registry."""
    return service_registry.get(EmbeddingProviderRegistry)


def get_embedding_provider(provider_name: str | None = None) -> EmbeddingProvider:
    """Return the selected embedding provider instance."""
    if provider_name is None:
        return service_registry.get(EmbeddingProvider)
    return embedding_provider_registry.get(provider_name)


def get_retrieval_engine() -> RetrievalEngine:
    """Return the shared retrieval engine instance."""
    return service_registry.get(RetrievalEngine)


def get_knowledge_repository() -> KnowledgeRepository:
    """Return the shared knowledge repository instance."""
    return service_registry.get(KnowledgeRepository)


def get_tool_registry() -> ToolRegistry:
    """Return the shared tool registry."""
    return service_registry.get(ToolRegistry)


def get_tool_executor() -> ToolExecutor:
    """Return the shared tool executor."""
    return service_registry.get(ToolExecutor)


def get_agent_registry() -> AgentRegistry:
    """Return the shared agent registry."""
    return service_registry.get(AgentRegistry)


def get_agent_runtime() -> AgentRuntime:
    """Return the shared agent runtime."""
    return service_registry.get(AgentRuntime)


def get_rag_service() -> RAGService:
    """Return the shared RAG service."""
    return service_registry.get(RAGService)


def get_streaming_engine() -> StreamingEngine:
    """Return the shared streaming engine."""
    return service_registry.get(StreamingEngine)


def get_document_ingestion_engine() -> DocumentIngestionEngine:
    """Return the shared document ingestion engine."""
    return service_registry.get(DocumentIngestionEngine)


def _create_database_provider() -> DatabaseProvider:
    return SupabaseProvider()


def _create_event_bus() -> EventBus:
    return InMemoryEventBus()


def _create_event_bus_service() -> EventBusService:
    return EventBusService(get_event_bus())


def _create_cache_manager() -> CacheManager:
    return CacheManager(InMemoryCacheBackend())


def _create_task_manager() -> BackgroundTaskManager:
    return BackgroundTaskManager(InMemoryTaskBackend())


def _create_metrics_provider() -> MetricsProvider:
    return InMemoryMetricsProvider()


def _create_supabase_auth_client() -> SupabaseAuthClient:
    return SupabaseAuthClient(get_database())


def _create_llm_provider() -> LLMProvider:
    return llm_provider_registry.get(settings.default_llm_provider)


def _create_memory_store() -> MemoryStore:
    return memory_store


def _create_memory_service() -> MemoryService:
    return MemoryService(get_memory_store(), get_event_bus_service())


def _create_vector_store() -> VectorStore:
    return vector_store


def _create_vector_service() -> VectorService:
    return VectorService(get_vector_store(), get_event_bus_service())


def _create_embedding_provider() -> EmbeddingProvider:
    return embedding_provider_registry.get(settings.default_embedding_provider or "openai")


def _create_retrieval_engine() -> RetrievalEngine:
    return RetrievalEngineService(
        get_embedding_provider(),
        get_vector_service(),
        get_event_bus_service(),
    )


def _create_knowledge_repository() -> KnowledgeRepository:
    return knowledge_repository


def _create_tool_executor() -> ToolExecutor:
    return ToolExecutor(get_tool_registry(), get_event_bus_service())


def _create_agent_runtime() -> AgentRuntime:
    return AgentRuntime(
        get_agent_registry(),
        get_tool_executor(),
        get_retrieval_engine(),
        get_event_bus_service(),
    )


def _create_context_builder() -> ContextBuilder:
    return DefaultContextBuilder(get_retrieval_engine(), get_memory_service())


def _create_prompt_augmenter() -> PromptAugmenter:
    return DefaultPromptAugmenter()


def _create_rag_service() -> RAGService:
    return RAGService(
        _create_context_builder(),
        _create_prompt_augmenter(),
        get_event_bus_service(),
    )


def _create_streaming_engine() -> StreamingEngine:
    return DefaultStreamingEngine()


def _create_document_ingestion_engine() -> DocumentIngestionEngine:
    return DocumentIngestionEngine()


def _create_ai_orchestrator() -> AIOrchestrator:
    return AIOrchestratorService(get_prompt_template_service(), get_llm_provider_registry())


def _create_auth_service() -> AuthService:
    return AuthService(get_supabase_auth_client())

register_instance(Settings, settings)
register_singleton(DatabaseProvider, _create_database_provider)
register_singleton(EventBus, _create_event_bus)
register_singleton(EventBusService, _create_event_bus_service)
register_singleton(CacheManager, _create_cache_manager)
register_singleton(BackgroundTaskManager, _create_task_manager)
register_singleton(MetricsProvider, _create_metrics_provider)
register_singleton(LLMProviderRegistry, lambda: llm_provider_registry)
register_singleton(LLMProvider, _create_llm_provider)
register_singleton(PromptRegistry, lambda: prompt_registry)
register_singleton(PromptTemplateService, lambda: PromptTemplateService(get_prompt_registry()))
register_singleton(ConversationStore, lambda: conversation_store)
register_singleton(ConversationEngine, lambda: ConversationEngineService(conversation_store))
register_singleton(MemoryStore, _create_memory_store)
register_singleton(MemoryService, _create_memory_service)
register_singleton(VectorStore, _create_vector_store)
register_singleton(VectorService, _create_vector_service)
register_singleton(EmbeddingProviderRegistry, lambda: embedding_provider_registry)
register_singleton(EmbeddingProvider, _create_embedding_provider)
register_singleton(RetrievalEngine, _create_retrieval_engine)
register_singleton(KnowledgeRepository, _create_knowledge_repository)
register_singleton(ToolRegistry, lambda: tool_registry)
register_singleton(ToolExecutor, _create_tool_executor)
register_singleton(AgentRegistry, lambda: agent_registry)
register_singleton(AgentRuntime, _create_agent_runtime)
register_singleton(RAGService, _create_rag_service)
register_singleton(StreamingEngine, _create_streaming_engine)
register_singleton(DocumentIngestionEngine, _create_document_ingestion_engine)
register_singleton(AIOrchestrator, _create_ai_orchestrator)
register_singleton(SupabaseAuthClient, _create_supabase_auth_client)
register_singleton(AuthService, _create_auth_service)
