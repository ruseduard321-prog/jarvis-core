from __future__ import annotations

import abc
from typing import Any

from backend.core.embedding_models import EmbeddingRequest, EmbeddingResponse


class EmbeddingProvider(abc.ABC):
    """Abstract interface for embedding generation providers."""

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """Return the provider name (e.g., 'openai', 'gemini', 'ollama')."""
        raise NotImplementedError

    @abc.abstractmethod
    async def initialize(self) -> None:
        """Initialize the provider (e.g., validate credentials, connect to service)."""
        raise NotImplementedError

    @abc.abstractmethod
    async def shutdown(self) -> None:
        """Shutdown the provider and release resources."""
        raise NotImplementedError

    @abc.abstractmethod
    async def health(self) -> bool:
        """Check provider health and availability."""
        raise NotImplementedError

    @abc.abstractmethod
    async def generate_embeddings(self, request: EmbeddingRequest) -> EmbeddingResponse:
        """Generate embeddings for the given texts."""
        raise NotImplementedError
