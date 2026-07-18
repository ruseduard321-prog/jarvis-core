from __future__ import annotations

from collections import defaultdict
from typing import Any, Callable

from backend.core.llm_provider import LLMProvider
from backend.core.llm_exceptions import LLMError


LLMProviderFactory = Callable[[], LLMProvider]


class LLMProviderRegistry:
    """Registry for named LLM provider implementations."""

    def __init__(self) -> None:
        self._providers: dict[str, LLMProviderFactory] = {}
        self._instances: dict[str, LLMProvider] = {}

    def register(self, name: str, factory: LLMProviderFactory) -> None:
        normalized = name.strip().lower()
        if not normalized:
            raise ValueError("Provider name must be set")
        self._providers[normalized] = factory

    def override(self, name: str, factory: LLMProviderFactory) -> None:
        self.register(name, factory)
        self._instances.pop(name.strip().lower(), None)

    def get(self, name: str) -> LLMProvider:
        normalized = name.strip().lower()
        factory = self._providers.get(normalized)
        if factory is None:
            raise LLMError(f"LLM provider not registered: {name}")

        if normalized not in self._instances:
            self._instances[normalized] = factory()
        return self._instances[normalized]

    def list_providers(self) -> list[str]:
        return sorted(self._providers.keys())
