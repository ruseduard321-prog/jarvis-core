from __future__ import annotations

import abc
import uuid
from datetime import datetime
from typing import Any, Protocol

from backend.core.conversation_exceptions import ConversationNotFoundError, ConversationStateError
from backend.core.conversation_models import Conversation, ConversationContext, ConversationMessage, ConversationState


class ConversationStore(abc.ABC):
    """Abstract interface for conversation storage."""

    @abc.abstractmethod
    async def create_conversation(self, title: str | None = None, metadata: dict[str, Any] | None = None) -> Conversation:
        raise NotImplementedError

    @abc.abstractmethod
    async def list_conversations(self) -> list[Conversation]:
        raise NotImplementedError

    @abc.abstractmethod
    async def get_conversation(self, conversation_id: str) -> Conversation:
        raise NotImplementedError

    @abc.abstractmethod
    async def append_message(self, conversation_id: str, message: ConversationMessage) -> Conversation:
        raise NotImplementedError

    @abc.abstractmethod
    async def update_metadata(self, conversation_id: str, metadata: dict[str, Any]) -> Conversation:
        raise NotImplementedError

    @abc.abstractmethod
    async def archive_conversation(self, conversation_id: str) -> Conversation:
        raise NotImplementedError

    @abc.abstractmethod
    async def delete_conversation(self, conversation_id: str) -> None:
        raise NotImplementedError


class InMemoryConversationStore(ConversationStore):
    """In-memory conversation store for development and foundation."""

    def __init__(self) -> None:
        self._conversations: dict[str, Conversation] = {}

    async def create_conversation(self, title: str | None = None, metadata: dict[str, Any] | None = None) -> Conversation:
        conversation_id = str(uuid.uuid4())
        now = datetime.utcnow()
        context = ConversationContext(
            conversation_id=conversation_id,
            title=title,
            state=ConversationState.ACTIVE,
            metadata=metadata or {},
            created_at=now,
            updated_at=now,
        )
        conversation = Conversation(context=context, messages=[])
        self._conversations[conversation_id] = conversation
        # DEBUG LOGGING
        print(f'\n=== POST /conversations ===')
        print(f"Store object: {hex(id(self))}")
        print(f"Dictionary object: {hex(id(self._conversations))}")
        print(f"Created: {conversation_id}")
        print()
        return conversation

    async def list_conversations(self) -> list[Conversation]:
        # DEBUG LOGGING
        print(f'\n=== GET /conversations ===')
        print(f"Store object: {hex(id(self))}")
        print(f"Dictionary object: {hex(id(self._conversations))}")
        print(f"Keys:")
        for key in self._conversations.keys():
            print(f"  - {key}")
        print()
        return list(self._conversations.values())

    async def get_conversation(self, conversation_id: str) -> Conversation:
        # DEBUG LOGGING
        print(f'\n=== GET /conversations/{{id}}/messages ===')
        print(f"Store object: {hex(id(self))}")
        print(f"Dictionary object: {hex(id(self._conversations))}")
        print(f"Keys:")
        for key in self._conversations.keys():
            print(f"  - {key}")
        print(f"Requested: {conversation_id}")
        print()
        conversation = self._conversations.get(conversation_id)
        if conversation is None:
            raise ConversationNotFoundError(f"Conversation not found: {conversation_id}")
        return conversation

    async def append_message(self, conversation_id: str, message: ConversationMessage) -> Conversation:
        conversation = await self.get_conversation(conversation_id)
        if conversation.context.state != ConversationState.ACTIVE:
            raise ConversationStateError("Cannot append messages to non-active conversation")

        updated_messages = conversation.messages + [message]
        updated_context = ConversationContext(
            **{
                **conversation.context.__dict__,
                "updated_at": datetime.utcnow(),
            }
        )
        updated_conversation = Conversation(context=updated_context, messages=updated_messages)
        self._conversations[conversation_id] = updated_conversation
        return updated_conversation

    async def update_metadata(self, conversation_id: str, metadata: dict[str, Any]) -> Conversation:
        conversation = await self.get_conversation(conversation_id)
        updated_context = ConversationContext(
            **{
                **conversation.context.__dict__,
                "metadata": {**conversation.context.metadata, **(metadata or {})},
                "updated_at": datetime.utcnow(),
            }
        )
        updated_conversation = Conversation(context=updated_context, messages=conversation.messages)
        self._conversations[conversation_id] = updated_conversation
        return updated_conversation

    async def archive_conversation(self, conversation_id: str) -> Conversation:
        conversation = await self.get_conversation(conversation_id)
        if conversation.context.state == ConversationState.DELETED:
            raise ConversationStateError("Cannot archive deleted conversation")

        updated_context = ConversationContext(
            **{
                **conversation.context.__dict__,
                "state": ConversationState.ARCHIVED,
                "updated_at": datetime.utcnow(),
            }
        )
        updated_conversation = Conversation(context=updated_context, messages=conversation.messages)
        self._conversations[conversation_id] = updated_conversation
        return updated_conversation

    async def delete_conversation(self, conversation_id: str) -> None:
        if conversation_id not in self._conversations:
            raise ConversationNotFoundError(f"Conversation not found: {conversation_id}")
        del self._conversations[conversation_id]
