from __future__ import annotations

from typing import Any

from backend.core.embedding_provider import EmbeddingProvider


class EmbeddingProviderRegistry:
    """Registry for managing multiple embedding provider implementations."""

    def __init__(self) -> None:
        self._providers: dict[str, EmbeddingProvider] = {}

    def register(self, provider: EmbeddingProvider) -> None:
        """Register an embedding provider by name."""
        self._providers[provider.name] = provider

    def get(self, provider_name: str | None = None) -> EmbeddingProvider:
        """Get a registered embedding provider."""
        if provider_name is None:
            provider_name = "openai"
        
        if provider_name not in self._providers:
            raise ValueError(f"Embedding provider not registered: {provider_name}")
        
        return self._providers[provider_name]

    def list_providers(self) -> list[str]:
        """List all registered embedding providers."""
        return list(self._providers.keys())
