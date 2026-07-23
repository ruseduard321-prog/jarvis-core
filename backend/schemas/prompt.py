from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, Field


# ============================================================
# PROMPT SCHEMAS
# ============================================================

class PromptCreateRequest(BaseModel):
    """Request to create a prompt."""

    name: str = Field(description="Prompt name")
    content: str = Field(description="Prompt content")
    category: str = Field(description="Prompt category (Chat, System, Coding, Analysis, Writing, Creative)")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Code Review Assistant",
                "content": "You are a code review expert. Review the following code for bugs, performance issues, and best practices.",
                "category": "Coding",
            }
        }


class PromptUpdateRequest(BaseModel):
    """Request to update a prompt."""

    name: str | None = Field(None, description="Updated name")
    content: str | None = Field(None, description="Updated content")
    category: str | None = Field(None, description="Updated category")
    favorite: bool | None = Field(None, description="Favorite status")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Enhanced Code Review",
                "favorite": True,
            }
        }


class PromptResponse(BaseModel):
    """Response for a prompt."""

    id: str = Field(description="Prompt ID")
    name: str = Field(description="Prompt name")
    content: str = Field(description="Prompt content")
    category: str = Field(description="Prompt category")
    favorite: bool = Field(description="Favorite status")
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "prompt_abc123",
                "name": "Code Review Assistant",
                "content": "You are a code review expert...",
                "category": "Coding",
                "favorite": True,
                "created_at": "2026-07-19T10:00:00Z",
                "updated_at": "2026-07-19T10:00:00Z",
            }
        }
