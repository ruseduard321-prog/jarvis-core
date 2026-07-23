from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal

AgentTaskStatus = Literal["pending", "running", "completed", "failed"]
AgentExecutionStatus = Literal["success", "partial", "failed"]


@dataclass(frozen=True)
class AgentTask:
    """Delegation task unit tracked by the orchestrator."""

    id: str
    requesting_agent: str
    target_agent: str
    objective: str
    reason: str
    context: dict[str, Any] = field(default_factory=dict)
    status: AgentTaskStatus = "pending"
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "requesting_agent": self.requesting_agent,
            "target_agent": self.target_agent,
            "objective": self.objective,
            "reason": self.reason,
            "context": self.context,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
        }


@dataclass(frozen=True)
class ExecutionContext:
    """Execution-scoped state shared across delegated agents."""

    conversation_id: str
    user_id: str | None = None
    memory: list[dict[str, Any]] = field(default_factory=list)
    documents: list[dict[str, Any]] = field(default_factory=list)
    media_assets: list[dict[str, Any]] = field(default_factory=list)
    artifacts: list[dict[str, Any]] = field(default_factory=list)
    execution_depth: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "conversation_id": self.conversation_id,
            "user_id": self.user_id,
            "memory": self.memory,
            "documents": self.documents,
            "media_assets": self.media_assets,
            "artifacts": self.artifacts,
            "execution_depth": self.execution_depth,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class AgentResult:
    """Standardized output contract for every agent execution."""

    summary: str
    status: AgentExecutionStatus
    output: Any = None
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    delegated_agents: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "summary": self.summary,
            "status": self.status,
            "output": self.output,
            "tool_calls": self.tool_calls,
            "delegated_agents": self.delegated_agents,
            "metadata": self.metadata,
        }
