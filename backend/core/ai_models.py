from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from backend.core.llm_models import LLMUsage
from backend.core.prompt_models import PromptTemplateMetadata


@dataclass(frozen=True)
class AIExecutionContext:
    """Context describing how the AI request was executed."""

    template_name: str
    template_version: str | None
    provider_name: str | None
    model: str
    variables: dict[str, Any] = field(default_factory=dict)
    options: dict[str, Any] = field(default_factory=dict)
    template_metadata: PromptTemplateMetadata | None = None


@dataclass(frozen=True)
class AIRequest:
    """Standardized request payload for the AI orchestrator."""

    template_name: str
    model: str
    variables: dict[str, Any] = field(default_factory=dict)
    provider_name: str | None = None
    template_version: str | None = None
    temperature: float | None = 1.0
    max_tokens: int | None = None
    options: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AIResponse:
    """Standardized response returned by the AI orchestrator."""

    provider_name: str
    model: str
    output: str
    usage: LLMUsage | None = None
    raw_response: Any | None = None
    execution_context: AIExecutionContext | None = None
