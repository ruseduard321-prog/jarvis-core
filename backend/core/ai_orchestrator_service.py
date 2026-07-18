from __future__ import annotations

from backend.core.ai_exceptions import (
    AIProviderSelectionError,
    AIPromptError,
    AIGenerationError,
)
from backend.core.ai_models import AIExecutionContext, AIRequest, AIResponse
from backend.core.llm_models import LLMMessage, LLMRequest
from backend.core.prompt_models import PromptTemplate
from backend.core.prompt_renderer import PromptTemplateRenderer
from backend.core.prompt_template_service import PromptTemplateService
from backend.core.llm_provider import LLMProvider
from backend.core.llm_provider_registry import LLMProviderRegistry


class AIOrchestratorService:
    """Default AI orchestrator implementation."""

    def __init__(
        self,
        prompt_service: PromptTemplateService,
        provider_registry: LLMProviderRegistry,
    ) -> None:
        self._prompt_service = prompt_service
        self._provider_registry = provider_registry

    async def execute(self, request: AIRequest) -> AIResponse:
        template = self._resolve_prompt_template(request.template_name, request.template_version)
        rendered_messages = self._render_prompt(template, request)
        provider = self._resolve_provider(request.provider_name)
        llm_request = self._build_llm_request(template, rendered_messages, request)

        try:
            llm_response = await provider.generate(llm_request)
        except Exception as exc:
            raise AIGenerationError("LLM provider execution failed") from exc

        return AIResponse(
            provider_name=provider.name,
            model=llm_response.model,
            output=llm_response.output,
            usage=llm_response.usage,
            raw_response=llm_response.raw_response,
            execution_context=AIExecutionContext(
                template_name=template.metadata.name,
                template_version=template.metadata.version,
                provider_name=provider.name,
                model=request.model,
                variables=request.variables,
                options=request.options,
                template_metadata=template.metadata,
            ),
        )

    def _resolve_prompt_template(self, name: str, version: str | None) -> PromptTemplate:
        try:
            return self._prompt_service.get_template(name, version=version)
        except Exception as exc:
            raise AIPromptError("Failed to resolve prompt template") from exc

    def _render_prompt(self, template: PromptTemplate, request: AIRequest) -> list[LLMMessage]:
        try:
            rendered_messages = PromptTemplateRenderer(template).render(request.variables)
            return [
                LLMMessage(role=message.role.value, content=message.content)
                for message in rendered_messages
            ]
        except Exception as exc:
            raise AIPromptError("Failed to render prompt template") from exc

    def _resolve_provider(self, provider_name: str | None) -> LLMProvider:
        try:
            return self._provider_registry.get(provider_name or get_settings().default_llm_provider)
        except Exception as exc:
            raise AIProviderSelectionError("Failed to select LLM provider") from exc

    def _build_llm_request(
        self,
        template: PromptTemplate,
        rendered_messages: list[LLMMessage],
        request: AIRequest,
    ) -> LLMRequest:
        provider_name = request.provider_name or get_settings().default_llm_provider
        return LLMRequest(
            model=request.model,
            messages=rendered_messages,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            provider=provider_name,
            options=request.options,
        )
