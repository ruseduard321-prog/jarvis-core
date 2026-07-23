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
from backend.core.prompt_library_service import PromptLibraryService
from backend.core.prompt_store import InMemoryPromptStore, PromptStore
from backend.core.tool import ToolRegistry
from backend.core.tool_registry_provider import tool_registry
from backend.core.tool_manager import ToolManager
from backend.tools.memory_tool import MemoryTool
from backend.tools.web_search_tool import WebSearchTool
from backend.tools.url_reader_tool import URLReaderTool
from backend.tools.pdf_reader_tool import PDFReaderTool
from backend.tools.markdown_reader_tool import MarkdownReaderTool
from backend.tools.text_reader_tool import TextReaderTool
from backend.tools.vision_tool import VisionTool
from backend.tools.image_generation_tool import ImageGenerationTool
from backend.services.tool_content_processing_service import ToolContentProcessingService
from backend.services.tool_resource_loader_service import ToolResourceLoaderService
from backend.services.search_provider import SearchProvider
from backend.services.brave_search_provider import BraveSearchProvider
from backend.services.vision_provider import VisionProvider
from backend.services.default_vision_provider import DefaultVisionProvider
from backend.services.image_generation_provider import ImageGenerationProvider
from backend.services.default_image_generation_provider import DefaultImageGenerationProvider
from backend.services.openai_image_generation_provider import OpenAIImageGenerationProvider
from backend.services.text_to_speech_provider import TextToSpeechProvider
from backend.services.default_text_to_speech_provider import DefaultTextToSpeechProvider
from backend.services.openai_text_to_speech_provider import OpenAITextToSpeechProvider
from backend.services.speech_to_text_provider import SpeechToTextProvider
from backend.services.default_speech_to_text_provider import DefaultSpeechToTextProvider
from backend.services.openai_speech_to_text_provider import OpenAISpeechToTextProvider
from backend.services.voice_generation_service import VoiceGenerationService
from backend.services.voice_direction_planner import DeterministicVoiceDirectionPlanner
from backend.services.narration_processing_service import NarrationProcessingService
from backend.services.music_generation_provider import MusicGenerationProvider
from backend.services.sound_effect_provider import SoundEffectProvider
from backend.services.local_audio_library_provider import LocalMusicLibraryProvider, LocalSoundEffectLibraryProvider
from backend.services.audio_timeline_planner import DeterministicAudioTimelinePlanner
from backend.services.audio_mixer_service import AudioMixerService
from backend.services.render_profile_registry import RenderProfileRegistry, build_default_render_profile_registry
from backend.services.audio_engine_service import AudioEngineService
from backend.services.thumbnail_generation_service import ThumbnailGenerationService
from backend.services.scene_image_generation_service import SceneImageGenerationService
from backend.services.scene_planning_service import ScenePlanningService
from backend.services.composition_planning_service import CompositionPlanningService
from backend.services.ai_director_provider import AIDirectorProvider, AgentRuntimeAIDirectorProvider
from backend.services.visual_identity_service import VisualIdentityService
from backend.services.character_reference_image_service import CharacterReferenceImageService
from backend.services.image_validation_service import ImageValidationService
from backend.services.subtitle_generation_service import SubtitleGenerationService
from backend.services.video_assembly_service import VideoAssemblyService
from backend.services.asset_packaging_service import AssetPackagingService
from backend.services.run_artifact_storage_service import RunArtifactStorageService
from backend.core.agent import Agent, AgentRegistry
from backend.core.agent_registry_provider import agent_registry
from backend.core.agent_orchestrator import AgentOrchestrator
from backend.core.agent_runtime import AgentRuntime
from backend.repositories.agent_repository import AgentRepository
from backend.services.agent_service import AgentService
from backend.core.rag_service import RAGService, ContextBuilder, DefaultContextBuilder, PromptAugmenter, DefaultPromptAugmenter
from backend.core.streaming_engine import DefaultStreamingEngine
from backend.core.streaming_models import StreamingEngine
from backend.core.ai_orchestrator import AIOrchestrator
from backend.core.ai_orchestrator_service import AIOrchestratorService
from backend.core.service_registry import service_registry
from backend.core.supabase_provider import SupabaseProvider
from backend.core.task_manager import BackgroundTaskManager, InMemoryTaskBackend
from backend.core.document_ingestion import DocumentIngestionEngine
from backend.services.dashboard_service import DashboardService
from backend.services.research_workflow_service import ResearchWorkflowService
from backend.services.content_finalization_workflow_service import ContentFinalizationWorkflowService
from backend.services.publishing_service import PublishingService
from backend.services.writer_workflow_service import WriterWorkflowService
from backend.services.strategy_workflow_service import StrategyWorkflowService
from backend.services.review_workflow_service import ReviewWorkflowService
from backend.services.media_workflow_service import MediaWorkflowService
from backend.services.publishing_package_workflow_service import PublishingPackageWorkflowService
from backend.services.workflow_manager import WorkflowManager
from backend.services.workflow_exporter import WorkflowExporter
from backend.core.workflow_history_store import WorkflowHistoryStore, InMemoryWorkflowHistoryStore
from backend.core.workflow_engine import WorkflowEngine
from backend.core.workflow_engine_models import WorkflowDefinition
from backend.services.youtube_production_workflow import (
    WORKFLOW_ID as YOUTUBE_PRODUCTION_WORKFLOW_ID,
    build_youtube_production_workflow,
)

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


def get_prompt_library_service() -> PromptLibraryService:
    """Return the shared prompt library service instance."""
    return service_registry.get(PromptLibraryService)


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


def get_tool_manager() -> ToolManager:
    """Return the shared tool manager."""
    return service_registry.get(ToolManager)


def get_agent_registry() -> AgentRegistry:
    """Return the shared agent registry."""
    return service_registry.get(AgentRegistry)


def get_agent_runtime() -> AgentRuntime:
    """Return the shared agent runtime."""
    return service_registry.get(AgentRuntime)


def get_agent_orchestrator() -> AgentOrchestrator:
    """Return the shared agent orchestrator."""
    return service_registry.get(AgentOrchestrator)


def get_agent_service() -> AgentService:
    """Return the shared agent service."""
    return service_registry.get(AgentService)


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


def get_dashboard_service() -> DashboardService:
    """Return the shared dashboard service instance."""
    return service_registry.get(DashboardService)


def get_research_workflow_service() -> ResearchWorkflowService:
    """Return the shared research workflow service instance."""
    return service_registry.get(ResearchWorkflowService)


def get_writer_workflow_service() -> WriterWorkflowService:
    """Return the shared writer workflow service instance."""
    return service_registry.get(WriterWorkflowService)


def get_content_finalization_workflow_service() -> ContentFinalizationWorkflowService:
    """Return the shared content finalization workflow service instance."""
    return service_registry.get(ContentFinalizationWorkflowService)


def get_publishing_service() -> PublishingService:
    """Return the shared YouTube publishing service instance."""
    return service_registry.get(PublishingService)


def get_strategy_workflow_service() -> StrategyWorkflowService:
    """Return the shared strategy workflow service instance."""
    return service_registry.get(StrategyWorkflowService)


def get_review_workflow_service() -> ReviewWorkflowService:
    """Return the shared review workflow service instance."""
    return service_registry.get(ReviewWorkflowService)


def get_media_workflow_service() -> MediaWorkflowService:
    """Return the shared media workflow service instance."""
    return service_registry.get(MediaWorkflowService)


def get_publishing_package_workflow_service() -> PublishingPackageWorkflowService:
    """Return the shared publishing package workflow service instance."""
    return service_registry.get(PublishingPackageWorkflowService)


def get_workflow_exporter() -> WorkflowExporter:
    """Return the shared workflow exporter instance."""
    return service_registry.get(WorkflowExporter)


def get_workflow_history_store() -> WorkflowHistoryStore:
    """Return the shared workflow history store instance."""
    return service_registry.get(WorkflowHistoryStore)


def get_workflow_engine() -> WorkflowEngine:
    """Return the shared generic workflow engine instance."""
    return service_registry.get(WorkflowEngine)


def get_workflow_manager() -> WorkflowManager:
    """Return the shared full-production workflow manager instance."""
    return service_registry.get(WorkflowManager)


def get_youtube_production_workflow_definition() -> WorkflowDefinition:
    """Build a fresh YouTube production workflow definition (steps hold shared singleton services)."""
    return _build_youtube_production_workflow_definition()


def get_image_generation_provider() -> ImageGenerationProvider:
    """Return the shared image generation provider instance."""
    return service_registry.get(ImageGenerationProvider)


def get_text_to_speech_provider() -> TextToSpeechProvider:
    """Return the shared text-to-speech provider instance."""
    return service_registry.get(TextToSpeechProvider)


def get_speech_to_text_provider() -> SpeechToTextProvider:
    """Return the shared speech-to-text provider instance."""
    return service_registry.get(SpeechToTextProvider)


def get_voice_generation_service() -> VoiceGenerationService:
    """Return the shared voice generation service instance."""
    return service_registry.get(VoiceGenerationService)


def get_music_generation_provider() -> MusicGenerationProvider:
    """Return the shared music generation provider instance."""
    return service_registry.get(MusicGenerationProvider)


def get_sound_effect_provider() -> SoundEffectProvider:
    """Return the shared sound effect provider instance."""
    return service_registry.get(SoundEffectProvider)


def get_audio_engine_service() -> AudioEngineService:
    """Return the shared audio engine service instance."""
    return service_registry.get(AudioEngineService)


def get_thumbnail_generation_service() -> ThumbnailGenerationService:
    """Return the shared thumbnail generation service instance."""
    return service_registry.get(ThumbnailGenerationService)


def get_scene_planning_service() -> ScenePlanningService:
    """Return the shared scene planning service instance."""
    return service_registry.get(ScenePlanningService)


def get_composition_planning_service() -> CompositionPlanningService:
    """Return the shared F27/F28 composition planning service instance."""
    return service_registry.get(CompositionPlanningService)


def get_ai_director_provider() -> AIDirectorProvider:
    """Return the shared F28 AI Director provider instance."""
    return service_registry.get(AIDirectorProvider)


def get_render_profile_registry() -> RenderProfileRegistry:
    """Return the shared F28A render profile registry instance."""
    return service_registry.get(RenderProfileRegistry)


def get_scene_image_generation_service() -> SceneImageGenerationService:
    """Return the shared scene image generation service instance."""
    return service_registry.get(SceneImageGenerationService)


def get_visual_identity_service() -> VisualIdentityService:
    """Return the shared F31 visual identity service instance."""
    return service_registry.get(VisualIdentityService)


def get_character_reference_image_service() -> CharacterReferenceImageService:
    """Return the shared F31 character reference image service instance."""
    return service_registry.get(CharacterReferenceImageService)


def get_image_validation_service() -> ImageValidationService:
    """Return the shared F31 image validation service instance."""
    return service_registry.get(ImageValidationService)


def get_subtitle_generation_service() -> SubtitleGenerationService:
    """Return the shared subtitle generation service instance."""
    return service_registry.get(SubtitleGenerationService)


def get_video_assembly_service() -> VideoAssemblyService:
    """Return the shared video assembly service instance."""
    return service_registry.get(VideoAssemblyService)


def get_run_artifact_storage_service() -> RunArtifactStorageService:
    """Return the shared run artifact storage service instance."""
    return service_registry.get(RunArtifactStorageService)


def get_asset_packaging_service() -> AssetPackagingService:
    """Return the shared asset packaging service instance."""
    return service_registry.get(AssetPackagingService)


def _create_dashboard_service() -> DashboardService:
    return DashboardService(
        conversation_store=get_conversation_store(),
        memory_store=get_memory_store(),
        event_bus_service=get_event_bus_service(),
    )


def _create_research_workflow_service() -> ResearchWorkflowService:
    return ResearchWorkflowService(
        conversation_engine=get_conversation_engine(),
        agent_runtime=get_agent_runtime(),
        agent_service=get_agent_service(),
        settings=get_settings(),
    )


def _create_writer_workflow_service() -> WriterWorkflowService:
    return WriterWorkflowService(
        conversation_engine=get_conversation_engine(),
        agent_runtime=get_agent_runtime(),
        agent_service=get_agent_service(),
        settings=get_settings(),
    )


def _create_strategy_workflow_service() -> StrategyWorkflowService:
    return StrategyWorkflowService(
        conversation_engine=get_conversation_engine(),
        agent_runtime=get_agent_runtime(),
        agent_service=get_agent_service(),
        settings=get_settings(),
    )


def _create_review_workflow_service() -> ReviewWorkflowService:
    return ReviewWorkflowService(
        conversation_engine=get_conversation_engine(),
        agent_runtime=get_agent_runtime(),
        agent_service=get_agent_service(),
        settings=get_settings(),
    )


def _create_media_workflow_service() -> MediaWorkflowService:
    return MediaWorkflowService(
        conversation_engine=get_conversation_engine(),
        agent_runtime=get_agent_runtime(),
        agent_service=get_agent_service(),
        settings=get_settings(),
    )


def _create_publishing_package_workflow_service() -> PublishingPackageWorkflowService:
    return PublishingPackageWorkflowService(
        conversation_engine=get_conversation_engine(),
        agent_runtime=get_agent_runtime(),
        agent_service=get_agent_service(),
        settings=get_settings(),
    )


def _create_content_finalization_workflow_service() -> ContentFinalizationWorkflowService:
    return ContentFinalizationWorkflowService(
        review_workflow_service=get_review_workflow_service(),
        media_workflow_service=get_media_workflow_service(),
        publishing_package_workflow_service=get_publishing_package_workflow_service(),
    )


def _create_publishing_service() -> PublishingService:
    return PublishingService(
        settings=get_settings(),
    )


def _create_workflow_exporter() -> WorkflowExporter:
    return WorkflowExporter(settings=get_settings())


def _create_workflow_history_store() -> WorkflowHistoryStore:
    return InMemoryWorkflowHistoryStore()


def _create_workflow_engine() -> WorkflowEngine:
    return WorkflowEngine(
        exporter=get_workflow_exporter(),
        history_store=get_workflow_history_store(),
    )


def _build_youtube_production_workflow_definition():
    return build_youtube_production_workflow(
        research_workflow_service=get_research_workflow_service(),
        strategy_workflow_service=get_strategy_workflow_service(),
        writer_workflow_service=get_writer_workflow_service(),
        review_workflow_service=get_review_workflow_service(),
        visual_identity_service=get_visual_identity_service(),
        character_reference_image_service=get_character_reference_image_service(),
        media_workflow_service=get_media_workflow_service(),
        publishing_package_workflow_service=get_publishing_package_workflow_service(),
        voice_generation_service=get_voice_generation_service(),
        thumbnail_generation_service=get_thumbnail_generation_service(),
        scene_planning_service=get_scene_planning_service(),
        composition_planning_service=get_composition_planning_service(),
        scene_image_generation_service=get_scene_image_generation_service(),
        subtitle_generation_service=get_subtitle_generation_service(),
        audio_engine_service=get_audio_engine_service(),
        video_assembly_service=get_video_assembly_service(),
        asset_packaging_service=get_asset_packaging_service(),
        run_artifact_storage_service=get_run_artifact_storage_service(),
        settings=get_settings(),
    )


def _create_voice_generation_service() -> VoiceGenerationService:
    return VoiceGenerationService(
        text_to_speech_provider=get_text_to_speech_provider(),
        settings=get_settings(),
        voice_direction_planner=DeterministicVoiceDirectionPlanner(),
        narration_processing_service=NarrationProcessingService(get_settings()),
    )


def _create_music_generation_provider() -> MusicGenerationProvider:
    return LocalMusicLibraryProvider(get_settings())


def _create_sound_effect_provider() -> SoundEffectProvider:
    return LocalSoundEffectLibraryProvider(get_settings())


def _create_render_profile_registry() -> RenderProfileRegistry:
    return build_default_render_profile_registry()


def _create_audio_engine_service() -> AudioEngineService:
    settings = get_settings()
    render_profile = get_render_profile_registry().get(settings.render_profile_name)
    return AudioEngineService(
        settings=settings,
        music_provider=get_music_generation_provider(),
        sound_effect_provider=get_sound_effect_provider(),
        timeline_planner=DeterministicAudioTimelinePlanner(settings),
        mixer=AudioMixerService(settings, render_profile=render_profile),
    )


def _create_thumbnail_generation_service() -> ThumbnailGenerationService:
    return ThumbnailGenerationService(
        image_generation_provider=get_image_generation_provider(),
        settings=get_settings(),
        image_validation_service=get_image_validation_service(),
    )


def _create_scene_planning_service() -> ScenePlanningService:
    return ScenePlanningService(
        conversation_engine=get_conversation_engine(),
        agent_runtime=get_agent_runtime(),
        agent_service=get_agent_service(),
        settings=get_settings(),
    )


def _create_ai_director_provider() -> AIDirectorProvider:
    return AgentRuntimeAIDirectorProvider(
        conversation_engine=get_conversation_engine(),
        agent_runtime=get_agent_runtime(),
        agent_service=get_agent_service(),
        settings=get_settings(),
    )


def _create_composition_planning_service() -> CompositionPlanningService:
    return CompositionPlanningService(settings=get_settings(), ai_director_provider=get_ai_director_provider())


def _create_scene_image_generation_service() -> SceneImageGenerationService:
    return SceneImageGenerationService(
        image_generation_provider=get_image_generation_provider(),
        settings=get_settings(),
        image_validation_service=get_image_validation_service(),
    )


def _create_visual_identity_service() -> VisualIdentityService:
    return VisualIdentityService(
        conversation_engine=get_conversation_engine(),
        agent_runtime=get_agent_runtime(),
        agent_service=get_agent_service(),
        settings=get_settings(),
    )


def _create_character_reference_image_service() -> CharacterReferenceImageService:
    return CharacterReferenceImageService(
        image_generation_provider=get_image_generation_provider(),
        settings=get_settings(),
        image_validation_service=get_image_validation_service(),
    )


def _create_image_validation_service() -> ImageValidationService:
    return ImageValidationService(
        openai_llm_provider=llm_provider_registry.get("openai"),
        settings=get_settings(),
    )


def _create_subtitle_generation_service() -> SubtitleGenerationService:
    return SubtitleGenerationService()


def _create_video_assembly_service() -> VideoAssemblyService:
    settings = get_settings()
    render_profile = get_render_profile_registry().get(settings.render_profile_name)
    return VideoAssemblyService(settings=settings, render_profile=render_profile)


def _create_run_artifact_storage_service() -> RunArtifactStorageService:
    return RunArtifactStorageService(settings=get_settings())


def _create_asset_packaging_service() -> AssetPackagingService:
    return AssetPackagingService()


def _create_text_to_speech_provider() -> TextToSpeechProvider:
    if get_settings().tts_provider == "openai":
        openai_provider = llm_provider_registry.get("openai")
        return OpenAITextToSpeechProvider(openai_llm_provider=openai_provider, settings=get_settings())
    return DefaultTextToSpeechProvider()


def _create_speech_to_text_provider() -> SpeechToTextProvider:
    if get_settings().stt_provider == "openai":
        openai_provider = llm_provider_registry.get("openai")
        return OpenAISpeechToTextProvider(openai_llm_provider=openai_provider, settings=get_settings())
    return DefaultSpeechToTextProvider()


def _create_workflow_manager() -> WorkflowManager:
    return WorkflowManager(
        llm_provider=get_llm_provider(),
        conversation_engine=get_conversation_engine(),
        workflow_engine=get_workflow_engine(),
        workflow_factories={
            YOUTUBE_PRODUCTION_WORKFLOW_ID: _build_youtube_production_workflow_definition,
        },
        workflow_history_store=get_workflow_history_store(),
    )


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


def _create_prompt_store() -> PromptStore:
    return InMemoryPromptStore()


def _create_prompt_library_service() -> PromptLibraryService:
    from backend.core.prompt_store import PromptStore
    return PromptLibraryService(service_registry.get(PromptStore), get_event_bus_service())


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


def _create_tool_content_processing_service() -> ToolContentProcessingService:
    return ToolContentProcessingService()


def _create_tool_resource_loader_service() -> ToolResourceLoaderService:
    return ToolResourceLoaderService()


def _create_search_provider() -> SearchProvider:
    settings = get_settings()
    return BraveSearchProvider(
        api_key=settings.brave_search_api_key,
        timeout_seconds=settings.brave_search_timeout_seconds,
    )


def _create_vision_provider() -> VisionProvider:
    return DefaultVisionProvider()


def _create_image_generation_provider() -> ImageGenerationProvider:
    if get_settings().image_provider == "openai":
        openai_provider = llm_provider_registry.get("openai")
        return OpenAIImageGenerationProvider(openai_llm_provider=openai_provider, settings=get_settings())
    return DefaultImageGenerationProvider()


def _create_tool_registry() -> ToolRegistry:
    registry = tool_registry
    registry.register(MemoryTool(get_memory_service()))
    registry.register(WebSearchTool(_create_search_provider()))
    registry.register(
        URLReaderTool(
            _create_tool_resource_loader_service(),
            _create_tool_content_processing_service(),
        )
    )
    registry.register(
        PDFReaderTool(
            _create_tool_resource_loader_service(),
            _create_tool_content_processing_service(),
        )
    )
    registry.register(
        MarkdownReaderTool(
            _create_tool_resource_loader_service(),
            _create_tool_content_processing_service(),
        )
    )
    registry.register(
        TextReaderTool(
            _create_tool_resource_loader_service(),
            _create_tool_content_processing_service(),
        )
    )
    registry.register(VisionTool(_create_vision_provider()))
    registry.register(ImageGenerationTool(get_image_generation_provider()))
    return registry


def _create_tool_manager() -> ToolManager:
    return ToolManager(get_tool_registry(), get_event_bus_service())


def _create_agent_runtime() -> AgentRuntime:
    return AgentRuntime(
        get_conversation_engine(),
        get_agent_orchestrator(),
    )


def _create_agent_orchestrator() -> AgentOrchestrator:
    return AgentOrchestrator(
        get_agent_service(),
        get_tool_registry(),
        get_tool_manager(),
        get_conversation_engine(),
        get_memory_service(),
        get_prompt_library_service(),
        get_llm_provider(),
        get_event_bus_service(),
    )


def _create_agent_repository() -> AgentRepository:
    return AgentRepository(get_database())


def _create_agent_service() -> AgentService:
    return AgentService(_create_agent_repository())


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
register_singleton(PromptStore, _create_prompt_store)
register_singleton(PromptLibraryService, _create_prompt_library_service)
register_singleton(VectorStore, _create_vector_store)
register_singleton(VectorService, _create_vector_service)
register_singleton(EmbeddingProviderRegistry, lambda: embedding_provider_registry)
register_singleton(EmbeddingProvider, _create_embedding_provider)
register_singleton(RetrievalEngine, _create_retrieval_engine)
register_singleton(KnowledgeRepository, _create_knowledge_repository)
register_singleton(ToolRegistry, _create_tool_registry)
register_singleton(ToolManager, _create_tool_manager)
register_singleton(AgentRegistry, lambda: agent_registry)
register_singleton(AgentService, _create_agent_service)
register_singleton(AgentOrchestrator, _create_agent_orchestrator)
register_singleton(AgentRuntime, _create_agent_runtime)
register_singleton(RAGService, _create_rag_service)
register_singleton(StreamingEngine, _create_streaming_engine)
register_singleton(DocumentIngestionEngine, _create_document_ingestion_engine)
register_singleton(AIOrchestrator, _create_ai_orchestrator)
register_singleton(SupabaseAuthClient, _create_supabase_auth_client)
register_singleton(AuthService, _create_auth_service)
register_singleton(DashboardService, _create_dashboard_service)
register_singleton(ResearchWorkflowService, _create_research_workflow_service)
register_singleton(WriterWorkflowService, _create_writer_workflow_service)
register_singleton(StrategyWorkflowService, _create_strategy_workflow_service)
register_singleton(ReviewWorkflowService, _create_review_workflow_service)
register_singleton(MediaWorkflowService, _create_media_workflow_service)
register_singleton(PublishingPackageWorkflowService, _create_publishing_package_workflow_service)
register_singleton(ContentFinalizationWorkflowService, _create_content_finalization_workflow_service)
register_singleton(PublishingService, _create_publishing_service)
register_singleton(WorkflowExporter, _create_workflow_exporter)
register_singleton(WorkflowHistoryStore, _create_workflow_history_store)
register_singleton(WorkflowEngine, _create_workflow_engine)
register_singleton(WorkflowManager, _create_workflow_manager)
register_singleton(ImageGenerationProvider, _create_image_generation_provider)
register_singleton(TextToSpeechProvider, _create_text_to_speech_provider)
register_singleton(SpeechToTextProvider, _create_speech_to_text_provider)
register_singleton(VoiceGenerationService, _create_voice_generation_service)
register_singleton(MusicGenerationProvider, _create_music_generation_provider)
register_singleton(SoundEffectProvider, _create_sound_effect_provider)
register_singleton(RenderProfileRegistry, _create_render_profile_registry)
register_singleton(AudioEngineService, _create_audio_engine_service)
register_singleton(ThumbnailGenerationService, _create_thumbnail_generation_service)
register_singleton(ScenePlanningService, _create_scene_planning_service)
register_singleton(AIDirectorProvider, _create_ai_director_provider)
register_singleton(CompositionPlanningService, _create_composition_planning_service)
register_singleton(ImageValidationService, _create_image_validation_service)
register_singleton(SceneImageGenerationService, _create_scene_image_generation_service)
register_singleton(VisualIdentityService, _create_visual_identity_service)
register_singleton(CharacterReferenceImageService, _create_character_reference_image_service)
register_singleton(SubtitleGenerationService, _create_subtitle_generation_service)
register_singleton(VideoAssemblyService, _create_video_assembly_service)
register_singleton(RunArtifactStorageService, _create_run_artifact_storage_service)
register_singleton(AssetPackagingService, _create_asset_packaging_service)
