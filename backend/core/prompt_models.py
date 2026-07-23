from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from datetime import datetime


class PromptRole(str, Enum):
    SYSTEM = "system"
    DEVELOPER = "developer"
    USER = "user"
    ASSISTANT = "assistant"


class PromptCategory(str, Enum):
    CHAT = "Chat"
    SYSTEM = "System"
    CODING = "Coding"
    ANALYSIS = "Analysis"
    WRITING = "Writing"
    CREATIVE = "Creative"


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


@dataclass
class Prompt:
    """A user-created reusable prompt for the library."""

    id: str
    name: str
    content: str
    category: PromptCategory
    favorite: bool = False
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
