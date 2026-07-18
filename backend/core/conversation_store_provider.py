from __future__ import annotations

from backend.core.conversation_store import ConversationStore, InMemoryConversationStore

conversation_store: ConversationStore = InMemoryConversationStore()
