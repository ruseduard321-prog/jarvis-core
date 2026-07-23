from __future__ import annotations

import abc
from typing import AsyncIterator

from backend.core.llm_exceptions import LLMError
from backend.core.llm_models import LLMRequest, LLMResponse


class LLMProvider(abc.ABC):
    """Abstract interface for all LLM providers."""

    @property
    @abc.abstractmethod
    def name(self) -> str:
        raise NotImplementedError

    async def initialize(self) -> None:
        """Initialize provider resources if required."""
        return None

    @abc.abstractmethod
    async def health(self) -> bool:
        raise NotImplementedError

    @abc.abstractmethod
    async def generate(self, request: LLMRequest) -> LLMResponse:
        raise NotImplementedError

    async def stream(self, request: LLMRequest) -> AsyncIterator[LLMResponse]:
        """Support streaming foundation with a single response by default."""
        response = await self.generate(request)
        yield LLMResponse(
            id=response.id,
            model=response.model,
            output=response.output,
            usage=response.usage,
            raw_response=response.raw_response,
            is_final=True,
        )

    async def shutdown(self) -> None:
        """Shutdown provider resources if required."""
        return None
