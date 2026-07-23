from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ToolMetadata:
    """Read-only metadata exposed for each registered tool."""

    slug: str
    name: str
    description: str
    capabilities: list[str]


@dataclass(frozen=True)
class ToolResult:
    """Normalized result returned by the tool manager."""

    success: bool
    output: Any | None = None
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ToolContext:
    """Context passed to tools during execution."""

    agent_id: str | None = None
    session_id: str | None = None
    conversation_id: str | None = None
    user_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
