from __future__ import annotations

import asyncio
from typing import Any

from backend.core.config import Settings
from backend.core.llm_exceptions import LLMGenerationError, LLMHealthError, LLMInitializationError
from backend.core.llm_models import LLMRequest, LLMResponse, LLMUsage
from backend.core.llm_provider import LLMProvider


class OpenAIProvider(LLMProvider):
    """OpenAI-compatible LLM provider implementation."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._initialized = False

    @property
    def name(self) -> str:
        return "openai"

    async def initialize(self) -> None:
        try:
            import openai  # type: ignore

            if self.settings.openai_api_key is None:
                raise LLMInitializationError("OPENAI_API_KEY is not configured")

            openai.api_key = self.settings.openai_api_key
            if self.settings.openai_api_base:
                openai.api_base = self.settings.openai_api_base
            if self.settings.openai_api_version:
                openai.api_version = self.settings.openai_api_version

            self._initialized = True
        except ImportError as exc:
            raise LLMInitializationError("OpenAI SDK is not installed") from exc
        except Exception as exc:
            raise LLMInitializationError("Failed to initialize OpenAI provider") from exc

    async def health(self) -> bool:
        if not self._initialized:
            await self.initialize()

        try:
            import openai  # type: ignore

            await asyncio.to_thread(openai.Model.list)
            return True
        except Exception as exc:
            raise LLMHealthError("OpenAI health check failed") from exc

    async def generate(self, request: LLMRequest) -> LLMResponse:
        if not self._initialized:
            await self.initialize()

        try:
            import openai  # type: ignore

            messages = [
                {"role": message.role, "content": message.content, **({"name": message.name} if message.name else {})}
                for message in request.messages
            ]

            completion = await asyncio.to_thread(
                lambda: openai.ChatCompletion.create(
                    model=request.model,
                    messages=messages,
                    temperature=request.temperature,
                    max_tokens=request.max_tokens,
                    **(request.options or {}),
                )
            )

            choice = completion.choices[0]
            content = getattr(choice.message, "content", "") if hasattr(choice, "message") else str(choice)
            usage_data = getattr(completion, "usage", None)
            usage = None
            if usage_data is not None:
                usage = LLMUsage(
                    prompt_tokens=getattr(usage_data, "prompt_tokens", 0) or 0,
                    completion_tokens=getattr(usage_data, "completion_tokens", 0) or 0,
                    total_tokens=getattr(usage_data, "total_tokens", 0) or 0,
                    extra={k: v for k, v in usage_data.items() if k not in {"prompt_tokens", "completion_tokens", "total_tokens"}},
                )

            return LLMResponse(
                id=str(getattr(completion, "id", "")),
                model=str(getattr(completion, "model", request.model)),
                output=content,
                usage=usage,
                raw_response=completion,
            )
        except Exception as exc:
            raise LLMGenerationError("OpenAI generation failed") from exc

    async def stream(self, request: LLMRequest) -> Any:
        if not self._initialized:
            await self.initialize()

        # Foundation-only streaming support; additional streaming implementations can be layered later.
        response = await self.generate(request)
        yield response

    async def shutdown(self) -> None:
        self._initialized = False
