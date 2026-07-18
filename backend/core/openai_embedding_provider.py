from __future__ import annotations

from typing import Any

from backend.core.embedding_models import EmbeddingRequest, EmbeddingResponse, EmbeddingUsage
from backend.core.embedding_provider import EmbeddingProvider
from backend.core.config import settings


class OpenAIEmbeddingProvider(EmbeddingProvider):
    """OpenAI-compatible embedding provider."""

    def __init__(self) -> None:
        self._name = "openai"
        self._model = settings.openai_embedding_model or "text-embedding-3-small"
        self._api_key = settings.openai_api_key
        self._client = None
        self._initialized = False

    @property
    def name(self) -> str:
        return self._name

    async def initialize(self) -> None:
        """Initialize OpenAI client (lazy-loaded on first use)."""
        if not self._api_key:
            raise RuntimeError("OpenAI API key not configured")
        self._initialized = True

    async def shutdown(self) -> None:
        """Shutdown OpenAI client."""
        self._initialized = False
        self._client = None

    async def health(self) -> bool:
        """Check health by verifying API key is set."""
        return bool(self._api_key) and self._initialized

    async def generate_embeddings(self, request: EmbeddingRequest) -> EmbeddingResponse:
        """Generate embeddings using OpenAI API."""
        if not self._initialized:
            await self.initialize()

        # Import here to avoid hard dependency on openai package
        try:
            import openai
        except ImportError:
            raise RuntimeError("OpenAI package not installed. Install with: pip install openai")

        client = openai.AsyncOpenAI(api_key=self._api_key)
        
        model = request.model or self._model
        response = await client.embeddings.create(
            input=request.texts,
            model=model,
            **request.options,
        )

        embeddings = [item.embedding for item in response.data]
        usage = EmbeddingUsage(
            input_tokens=response.usage.prompt_tokens if response.usage else None,
            output_tokens=response.usage.completion_tokens if response.usage else None,
            total_tokens=response.usage.total_tokens if response.usage else None,
        )

        return EmbeddingResponse(
            embeddings=embeddings,
            model=response.model,
            usage=usage,
            raw_response=response.model_dump(),
        )
