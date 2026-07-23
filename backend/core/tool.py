from __future__ import annotations

import abc
from typing import Any

from backend.core.tool_models import ToolContext, ToolMetadata, ToolResult


class Tool(abc.ABC):
    """Minimal contract implemented by every tool."""

    @property
    @abc.abstractmethod
    def slug(self) -> str:
        """Stable tool identifier used for registry lookup and APIs."""
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """Human-readable tool name."""
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def description(self) -> str:
        """Short description for discovery surfaces."""
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def capabilities(self) -> list[str]:
        """Stable capability identifiers exposed by the tool."""
        raise NotImplementedError

    @abc.abstractmethod
    async def execute(self, args: dict[str, Any], context: ToolContext) -> ToolResult:
        """Execute the tool with given arguments and context."""
        raise NotImplementedError


class ToolRegistry:
    """Registry for managing available tools."""

    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        """Register a tool by slug."""
        self._tools[tool.slug] = tool

    def unregister(self, tool_slug: str) -> None:
        """Unregister a tool by slug."""
        if tool_slug in self._tools:
            del self._tools[tool_slug]

    def get(self, tool_slug: str) -> Tool:
        """Get a registered tool by slug."""
        if tool_slug not in self._tools:
            raise ValueError(f"Tool not registered: {tool_slug}")
        return self._tools[tool_slug]

    def find_by_capability(self, capability: str) -> list[Tool]:
        """Find registered tools that expose the requested capability."""
        return [tool for tool in self._tools.values() if capability in tool.capabilities]

    def list_tools(self) -> list[ToolMetadata]:
        """List all registered tools with read-only metadata."""
        return [
            ToolMetadata(
                slug=t.slug,
                name=t.name,
                description=t.description,
                capabilities=t.capabilities,
            )
            for t in self._tools.values()
        ]
