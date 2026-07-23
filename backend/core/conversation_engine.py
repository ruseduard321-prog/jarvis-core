from __future__ import annotations

from typing import Protocol

from backend.core.conversation_models import Conversation, ConversationMessage


class ConversationEngine(Protocol):
    """Abstract conversation engine interface."""

    async def create_conversation(self, title: str | None = None, metadata: dict[str, object] | None = None) -> Conversation:
        raise NotImplementedError

    async def list_conversations(self) -> list[Conversation]:
        raise NotImplementedError

    async def load_conversation(self, conversation_id: str) -> Conversation:
        raise NotImplementedError

    async def append_message(self, conversation_id: str, message: ConversationMessage) -> Conversation:
        raise NotImplementedError

    async def update_metadata(self, conversation_id: str, metadata: dict[str, object]) -> Conversation:
        raise NotImplementedError

    async def archive_conversation(self, conversation_id: str) -> Conversation:
        raise NotImplementedError

    async def delete_conversation(self, conversation_id: str) -> None:
        raise NotImplementedError
