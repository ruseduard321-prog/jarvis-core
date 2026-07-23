from __future__ import annotations

from backend.core.conversation_exceptions import (
    ConversationNotFoundError,
    ConversationStateError,
)
from backend.core.conversation_engine import ConversationEngine
from backend.core.conversation_models import Conversation, ConversationContext, ConversationMessage
from backend.core.conversation_store import ConversationStore


class ConversationEngineService(ConversationEngine):
    """Default conversation engine implementation."""

    def __init__(self, store: ConversationStore) -> None:
        self._store = store

    async def create_conversation(self, title: str | None = None, metadata: dict[str, object] | None = None) -> Conversation:
        return await self._store.create_conversation(title=title, metadata=metadata)

    async def list_conversations(self) -> list[Conversation]:
        return await self._store.list_conversations()

    async def load_conversation(self, conversation_id: str) -> Conversation:
        return await self._store.get_conversation(conversation_id)

    async def append_message(self, conversation_id: str, message: ConversationMessage) -> Conversation:
        return await self._store.append_message(conversation_id, message)

    async def update_metadata(self, conversation_id: str, metadata: dict[str, object]) -> Conversation:
        return await self._store.update_metadata(conversation_id, metadata)

    async def archive_conversation(self, conversation_id: str) -> Conversation:
        return await self._store.archive_conversation(conversation_id)

    async def delete_conversation(self, conversation_id: str) -> None:
        await self._store.delete_conversation(conversation_id)
