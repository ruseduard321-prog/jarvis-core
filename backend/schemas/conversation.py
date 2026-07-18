from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, Field


# ============================================================
# CONVERSATION SCHEMAS
# ============================================================

class ConversationCreateRequest(BaseModel):
    """Request to create a new conversation."""

    title: str | None = Field(None, description="Optional conversation title")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Optional metadata")

    class Config:
        json_schema_extra = {
            "example": {
                "title": "Project Planning",
                "metadata": {"project_id": "proj_123", "team": "engineering"},
            }
        }


class ConversationUpdateRequest(BaseModel):
    """Request to update a conversation."""

    title: str | None = Field(None, description="New conversation title")
    metadata: dict[str, Any] | None = Field(None, description="Updated metadata")

    class Config:
        json_schema_extra = {
            "example": {
                "title": "Updated Title",
                "metadata": {"archived": True},
            }
        }


class ConversationResponse(BaseModel):
    """Response for a conversation."""

    id: str = Field(description="Conversation ID")
    title: str | None = Field(None, description="Conversation title")
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Metadata")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "conv_abc123",
                "title": "Project Planning",
                "created_at": "2026-07-18T10:00:00Z",
                "updated_at": "2026-07-18T10:05:00Z",
                "metadata": {"project_id": "proj_123"},
            }
        }


# ============================================================
# MESSAGE SCHEMAS
# ============================================================

class MessageCreateRequest(BaseModel):
    """Request to add a message to a conversation."""

    content: str = Field(description="Message content")
    role: str = Field(default="user", description="Message role (user, assistant, system)")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Optional metadata")

    class Config:
        json_schema_extra = {
            "example": {
                "content": "What are the project milestones?",
                "role": "user",
                "metadata": {"source": "web_ui"},
            }
        }


class MessageResponse(BaseModel):
    """Response for a message."""

    id: str = Field(description="Message ID")
    conversation_id: str = Field(description="Conversation ID")
    content: str = Field(description="Message content")
    role: str = Field(description="Message role")
    created_at: datetime = Field(description="Creation timestamp")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Metadata")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "msg_xyz789",
                "conversation_id": "conv_abc123",
                "content": "The milestones are Q3 and Q4 2026.",
                "role": "assistant",
                "created_at": "2026-07-18T10:01:00Z",
                "metadata": {},
            }
        }


# ============================================================
# CHAT COMPLETION SCHEMAS
# ============================================================

class ChatCompletionRequest(BaseModel):
    """Request for chat completion (query)."""

    conversation_id: str = Field(description="Conversation ID")
    message: str = Field(description="User message")
    use_rag: bool = Field(default=True, description="Whether to use RAG for context")
    stream: bool = Field(default=False, description="Whether to stream response")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Optional metadata")

    class Config:
        json_schema_extra = {
            "example": {
                "conversation_id": "conv_abc123",
                "message": "Summarize the project timeline",
                "use_rag": True,
                "stream": False,
                "metadata": {"model": "gpt-4"},
            }
        }


class ChatCompletionResponse(BaseModel):
    """Response for chat completion."""

    conversation_id: str = Field(description="Conversation ID")
    user_message_id: str = Field(description="User message ID")
    assistant_message_id: str = Field(description="Assistant message ID")
    content: str = Field(description="Assistant response")
    tokens_used: int | None = Field(None, description="Tokens used in completion")
    rag_context_used: bool = Field(description="Whether RAG context was used")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Response metadata")

    class Config:
        json_schema_extra = {
            "example": {
                "conversation_id": "conv_abc123",
                "user_message_id": "msg_user_123",
                "assistant_message_id": "msg_asst_456",
                "content": "The project timeline spans Q3-Q4 2026 with key deliverables...",
                "tokens_used": 245,
                "rag_context_used": True,
                "metadata": {"model": "gpt-4"},
            }
        }


class ChatStreamEvent(BaseModel):
    """Server-sent event for streaming chat."""

    event: str = Field(description="Event type (start, token, end, error)")
    data: str | None = Field(None, description="Event data (token or error)")
    message_id: str | None = Field(None, description="Message ID")
