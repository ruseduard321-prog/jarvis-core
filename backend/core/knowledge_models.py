from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class KnowledgeSourceType(str, Enum):
    """Type of knowledge source."""

    CONVERSATION = "conversation"
    DOCUMENT = "document"
    WEBSITE = "website"
    API = "api"
    MEMORY = "memory"
    USER_INPUT = "user_input"
    CUSTOM = "custom"


@dataclass(frozen=True)
class KnowledgeSource:
    """Metadata about the origin of knowledge."""

    type: KnowledgeSourceType
    identifier: str
    url: str | None = None
    created_at: datetime | None = None
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class KnowledgeChunk:
    """Discrete chunk of knowledge content."""

    id: str
    document_id: str
    content: str
    chunk_index: int
    source: KnowledgeSource
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime | None = None


@dataclass(frozen=True)
class KnowledgeDocument:
    """A document storing knowledge units."""

    id: str
    title: str
    content: str
    source: KnowledgeSource
    created_at: datetime
    updated_at: datetime
    chunks: list[KnowledgeChunk] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
