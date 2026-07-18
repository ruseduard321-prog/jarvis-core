from __future__ import annotations

from backend.core.prompt_exceptions import PromptTemplateNotFoundError
from backend.core.prompt_models import PromptTemplate
from backend.core.prompt_store import PromptStore


class PromptRegistry:
    """Registry that resolves prompt templates by name and version."""

    def __init__(self, store: PromptStore) -> None:
        self._store = store

    def register_template(self, template: PromptTemplate) -> None:
        self._store.add_template(template)

    def get_template(self, name: str, version: str | None = None) -> PromptTemplate:
        return self._store.get_template(name, version=version)

    def list_templates(self, name: str | None = None) -> list[PromptTemplate]:
        return self._store.list_templates(name=name)

    def list_versions(self, name: str) -> list[str]:
        templates = self._store.list_templates(name=name)
        return [template.metadata.version for template in templates]
