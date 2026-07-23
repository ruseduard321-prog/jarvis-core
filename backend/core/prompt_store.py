from __future__ import annotations

import abc
import uuid
from typing import Iterable
from datetime import datetime

from backend.core.prompt_exceptions import PromptTemplateNotFoundError
from backend.core.prompt_models import PromptTemplate, Prompt, PromptCategory


class PromptStore(abc.ABC):
    """Storage abstraction for prompt templates and user prompts."""

    # Template methods
    @abc.abstractmethod
    def add_template(self, template: PromptTemplate) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def get_template(self, name: str, version: str | None = None) -> PromptTemplate:
        raise NotImplementedError

    @abc.abstractmethod
    def list_templates(self, name: str | None = None) -> list[PromptTemplate]:
        raise NotImplementedError

    # Prompt library methods
    @abc.abstractmethod
    async def create_prompt(self, name: str, content: str, category: PromptCategory) -> Prompt:
        raise NotImplementedError

    @abc.abstractmethod
    async def read_prompt(self, prompt_id: str) -> Prompt:
        raise NotImplementedError

    @abc.abstractmethod
    async def update_prompt(self, prompt_id: str, name: str | None = None, content: str | None = None, category: PromptCategory | None = None, favorite: bool | None = None) -> Prompt:
        raise NotImplementedError

    @abc.abstractmethod
    async def delete_prompt(self, prompt_id: str) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    async def list_prompts(self) -> list[Prompt]:
        raise NotImplementedError


class InMemoryPromptStore(PromptStore):
    """In-memory prompt template and user prompt store for development and production foundation."""

    def __init__(self) -> None:
        self._templates: dict[str, dict[str, PromptTemplate]] = {}
        self._prompts: dict[str, Prompt] = {}

    # Template methods
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

    # Prompt library methods
    async def create_prompt(self, name: str, content: str, category: PromptCategory) -> Prompt:
        prompt_id = str(uuid.uuid4())
        prompt = Prompt(
            id=prompt_id,
            name=name,
            content=content,
            category=category,
            favorite=False,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        self._prompts[prompt_id] = prompt
        return prompt

    async def read_prompt(self, prompt_id: str) -> Prompt:
        if prompt_id not in self._prompts:
            raise KeyError(f"Prompt not found: {prompt_id}")
        return self._prompts[prompt_id]

    async def update_prompt(self, prompt_id: str, name: str | None = None, content: str | None = None, category: PromptCategory | None = None, favorite: bool | None = None) -> Prompt:
        if prompt_id not in self._prompts:
            raise KeyError(f"Prompt not found: {prompt_id}")
        
        prompt = self._prompts[prompt_id]
        updated_prompt = Prompt(
            id=prompt.id,
            name=name if name is not None else prompt.name,
            content=content if content is not None else prompt.content,
            category=category if category is not None else prompt.category,
            favorite=favorite if favorite is not None else prompt.favorite,
            created_at=prompt.created_at,
            updated_at=datetime.utcnow(),
        )
        self._prompts[prompt_id] = updated_prompt
        return updated_prompt

    async def delete_prompt(self, prompt_id: str) -> None:
        if prompt_id not in self._prompts:
            raise KeyError(f"Prompt not found: {prompt_id}")
        del self._prompts[prompt_id]

    async def list_prompts(self) -> list[Prompt]:
        # Return sorted by updated_at DESC (newest first)
        return sorted(self._prompts.values(), key=lambda p: p.updated_at, reverse=True)
