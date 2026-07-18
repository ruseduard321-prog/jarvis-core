from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class AgentStatus(str, Enum):
    """Status of agent execution."""

    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class AgentContext:
    """Context passed to agent during execution."""

    conversation_id: str | None = None
    user_id: str | None = None
    session_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AgentExecution:
    """Execution trace of an agent."""

    agent_id: str
    execution_id: str
    status: AgentStatus
    input_message: str | None = None
    output_message: str | None = None
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    steps: int = 0
    started_at: datetime | None = None
    completed_at: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AgentResponse:
    """Response from agent execution."""

    agent_id: str
    status: AgentStatus
    message: str | None = None
    execution_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AgentSession:
    """Agent execution session."""

    session_id: str
    agent_id: str
    conversation_id: str | None = None
    user_id: str | None = None
    created_at: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
