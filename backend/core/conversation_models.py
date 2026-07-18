from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class ConversationRole(str, Enum):
    SYSTEM = "system"
    DEVELOPER = "developer"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class ConversationState(str, Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"


@dataclass(frozen=True)
class ConversationMessage:
    """A single message inside a conversation."""

    id: str
    role: ConversationRole
    content: str
    created_at: datetime
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ConversationContext:
    """Context metadata for a conversation session."""

    conversation_id: str
    title: str | None = None
    state: ConversationState = ConversationState.ACTIVE
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(frozen=True)
class Conversation:
    """A complete conversation record."""

    context: ConversationContext
    messages: list[ConversationMessage] = field(default_factory=list)
