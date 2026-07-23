from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class LLMMessage:
    """A standardized message for model interactions."""

    role: str
    content: str
    name: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class LLMUsage:
    """Token usage information returned by an LLM provider."""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class LLMRequest:
    """A standardized request payload for LLM providers."""

    model: str
    messages: list[LLMMessage]
    temperature: float | None = 1.0
    max_tokens: int | None = None
    provider: str | None = None
    options: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class LLMResponse:
    """A standardized response from an LLM provider.

    When yielded from `LLMProvider.stream()`, each chunk's `output` is an incremental
    delta (not the accumulated text). The terminal chunk carries `is_final=True` along
    with the completion's id/model/usage; its `output` is typically empty.
    """

    id: str
    model: str
    output: str
    usage: LLMUsage | None = None
    raw_response: Any | None = None
    is_final: bool = False
