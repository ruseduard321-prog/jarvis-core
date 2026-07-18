from __future__ import annotations

from backend.core.prompt_registry import PromptRegistry
from backend.core.prompt_models import PromptTemplate


class PromptTemplateService:
    """Service layer for prompt template registration and resolution."""

    def __init__(self, registry: PromptRegistry) -> None:
        self._registry = registry

    def register_template(self, template: PromptTemplate) -> None:
        self._registry.register_template(template)

    def get_template(self, name: str, version: str | None = None) -> PromptTemplate:
        return self._registry.get_template(name, version=version)

    def list_templates(self, name: str | None = None) -> list[PromptTemplate]:
        return self._registry.list_templates(name=name)

    def list_versions(self, name: str) -> list[str]:
        return self._registry.list_versions(name)
