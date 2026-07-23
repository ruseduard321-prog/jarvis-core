"""Dashboard response schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class StatusIndicator(BaseModel):
    """System component status."""
    name: str
    status: str  # "online" | "offline" | "degraded"
    message: str
    timestamp: datetime


class SystemStatus(BaseModel):
    """Overall system status."""
    status: str  # "healthy" | "degraded" | "unhealthy"
    backend: StatusIndicator
    database: StatusIndicator
    ai_provider: StatusIndicator
    timestamp: datetime


class Statistics(BaseModel):
    """Dashboard statistics."""
    total_conversations: int
    total_messages: int
    total_knowledge_items: int
    total_agents: int
    total_documents: int
    today_activity: int


class ConversationSummary(BaseModel):
    """Recent conversation summary."""
    id: str
    title: str | None
    message_count: int
    last_message_at: datetime
    status: str


class ActivityEvent(BaseModel):
    """Recent activity event."""
    id: str
    type: str
    timestamp: datetime
    description: str
    metadata: dict[str, Any]


class QuickAction(BaseModel):
    """Quick action card."""
    id: str
    label: str
    description: str
    icon: str
    href: str


class DashboardResponse(BaseModel):
    """Complete dashboard response."""
    statistics: Statistics
    recent_conversations: list[ConversationSummary]
    activity: list[ActivityEvent]
    system_status: SystemStatus
    quick_actions: list[QuickAction]
    timestamp: datetime
