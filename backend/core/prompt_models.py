from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class PromptRole(str, Enum):
    SYSTEM = "system"
    DEVELOPER = "developer"
    USER = "user"
    ASSISTANT = "assistant"


@dataclass(frozen=True)
class PromptMessage:
    """A single prompt message with a role and templated content."""

    role: PromptRole
    content: str
    name: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PromptTemplateMetadata:
    """Template metadata used for versioning and discovery."""

    name: str
    version: str = "1.0"
    description: str | None = None
    tags: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class PromptTemplate:
    """A reusable prompt template containing a sequence of messages."""

    metadata: PromptTemplateMetadata
    messages: list[PromptMessage]
