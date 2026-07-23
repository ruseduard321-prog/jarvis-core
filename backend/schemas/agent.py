from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, Field


class AgentCreateRequest(BaseModel):
    """Request to create an agent."""

    slug: str = Field(description="Stable agent slug")
    name: str = Field(description="Agent name")
    mission: str = Field(description="Operational mission")
    allowed_delegations: list[str] = Field(default_factory=list, description="Allowed agent IDs for delegation")


class AgentUpdateRequest(BaseModel):
    """Request to update an agent."""

    slug: str | None = Field(None, description="Updated stable agent slug")
    name: str | None = Field(None, description="Updated agent name")
    mission: str | None = Field(None, description="Updated operational mission")
    allowed_delegations: list[str] | None = Field(None, description="Allowed agent IDs for delegation")
    is_active: bool | None = Field(None, description="Whether the agent is active")


class AgentResponse(BaseModel):
    """Response model for persisted agents."""

    id: str = Field(description="Agent ID")
    slug: str = Field(description="Stable agent slug")
    owner_user_id: str = Field(description="Agent owner user ID")
    name: str = Field(description="Agent name")
    mission: str = Field(description="Operational mission")
    allowed_delegations: list[str] = Field(default_factory=list, description="Allowed agent IDs for delegation")
    is_active: bool = Field(description="Whether the agent is active")
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")
