from __future__ import annotations

from backend.core.config import settings
from backend.core.llm_provider_registry import LLMProviderRegistry
from backend.core.openai_llm_provider import OpenAIProvider

llm_provider_registry = LLMProviderRegistry()
llm_provider_registry.register("openai", lambda: OpenAIProvider(settings))
