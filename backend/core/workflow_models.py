from __future__ import annotations

import abc
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class WorkflowNodeType(str, Enum):
    """Type of workflow node."""

    START = "start"
    END = "end"
    TASK = "task"
    DECISION = "decision"
    PARALLEL = "parallel"
    MERGE = "merge"


class WorkflowStatus(str, Enum):
    """Status of workflow execution."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class WorkflowNode:
    """A node in the workflow DAG."""

    id: str
    name: str
    node_type: WorkflowNodeType
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class WorkflowEdge:
    """An edge connecting two nodes in the workflow."""

    source_id: str
    target_id: str
    condition: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Workflow:
    """A DAG-based workflow definition."""

    id: str
    name: str
    description: str | None = None
    nodes: list[WorkflowNode] = field(default_factory=list)
    edges: list[WorkflowEdge] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class WorkflowContext:
    """Context during workflow execution."""

    workflow_id: str
    execution_id: str
    user_id: str | None = None
    conversation_id: str | None = None
    state: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class WorkflowExecution:
    """Execution trace of a workflow."""

    workflow_id: str
    execution_id: str
    status: WorkflowStatus
    current_node_id: str | None = None
    completed_nodes: list[str] = field(default_factory=list)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class WorkflowRunner(abc.ABC):
    """Abstract interface for running workflows."""

    @abc.abstractmethod
    async def run(self, workflow: Workflow, context: WorkflowContext) -> WorkflowExecution:
        """Execute a workflow."""
        raise NotImplementedError

    @abc.abstractmethod
    async def cancel(self, execution_id: str) -> None:
        """Cancel an ongoing workflow execution."""
        raise NotImplementedError
