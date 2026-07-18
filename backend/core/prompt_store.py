from __future__ import annotations

import abc
from typing import Iterable

from backend.core.prompt_exceptions import PromptTemplateNotFoundError
from backend.core.prompt_models import PromptTemplate


class PromptStore(abc.ABC):
    """Storage abstraction for prompt templates."""

    @abc.abstractmethod
    def add_template(self, template: PromptTemplate) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def get_template(self, name: str, version: str | None = None) -> PromptTemplate:
        raise NotImplementedError

    @abc.abstractmethod
    def list_templates(self, name: str | None = None) -> list[PromptTemplate]:
        raise NotImplementedError


class InMemoryPromptStore(PromptStore):
    """In-memory prompt template store for development and production foundation."""

    def __init__(self) -> None:
        self._templates: dict[str, dict[str, PromptTemplate]] = {}

    def add_template(self, template: PromptTemplate) -> None:
        name = template.metadata.name.strip().lower()
        version = template.metadata.version.strip()
        versions = self._templates.setdefault(name, {})
        versions[version] = template

    def get_template(self, name: str, version: str | None = None) -> PromptTemplate:
        normalized = name.strip().lower()
        versions = self._templates.get(normalized)
        if versions is None:
            raise PromptTemplateNotFoundError(f"Prompt template not found: {name}")

        if version is None:
            latest_version = sorted(versions.keys())[-1]
            return versions[latest_version]

        template = versions.get(version.strip())
        if template is None:
            raise PromptTemplateNotFoundError(f"Prompt template not found: {name} version {version}")
        return template

    def list_templates(self, name: str | None = None) -> list[PromptTemplate]:
        if name is None:
            return [template for versions in self._templates.values() for template in versions.values()]

        normalized = name.strip().lower()
        versions = self._templates.get(normalized, {})
        return list(versions.values())
