from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable


class ToolCategory(str, Enum):
    """Category of tool for organization and access control."""

    SEARCH = "search"
    MEMORY = "memory"
    KNOWLEDGE = "knowledge"
    COMPUTATION = "computation"
    EXTERNAL = "external"
    SYSTEM = "system"


@dataclass(frozen=True)
class ToolParameter:
    """Definition of a tool parameter."""

    name: str
    type: str  # e.g., "string", "number", "boolean", "array"
    description: str | None = None
    required: bool = True
    default: Any | None = None
    enum_values: list[Any] | None = None


@dataclass(frozen=True)
class ToolMetadata:
    """Metadata for a tool."""

    name: str
    description: str
    category: ToolCategory
    parameters: list[ToolParameter] = field(default_factory=list)
    enabled: bool = True
    timeout_seconds: int | None = None
    requires_permission: str | None = None
    tags: list[str] = field(default_factory=list)
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ToolResult:
    """Result from tool execution."""

    success: bool
    output: Any | None = None
    error: str | None = None
    execution_time_ms: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ToolContext:
    """Context passed to tools during execution."""

    agent_id: str | None = None
    session_id: str | None = None
    conversation_id: str | None = None
    user_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
