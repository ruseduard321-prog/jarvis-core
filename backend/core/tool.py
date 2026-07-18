from __future__ import annotations

import abc
from typing import Any, Callable

from backend.core.tool_models import ToolContext, ToolMetadata, ToolResult


class Tool(abc.ABC):
    """Abstract interface for tools that can be called by agents."""

    @property
    @abc.abstractmethod
    def metadata(self) -> ToolMetadata:
        """Return tool metadata."""
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
        """Register a tool by name."""
        self._tools[tool.metadata.name] = tool

    def unregister(self, tool_name: str) -> None:
        """Unregister a tool by name."""
        if tool_name in self._tools:
            del self._tools[tool_name]

    def get(self, tool_name: str) -> Tool:
        """Get a registered tool by name."""
        if tool_name not in self._tools:
            raise ValueError(f"Tool not registered: {tool_name}")
        return self._tools[tool_name]

    def list_tools(self, enabled_only: bool = True) -> list[ToolMetadata]:
        """List all registered tools, optionally filtered by enabled status."""
        tools = list(self._tools.values())
        if enabled_only:
            tools = [t for t in tools if t.metadata.enabled]
        return [t.metadata for t in tools]

    def find_by_category(self, category: str) -> list[ToolMetadata]:
        """Find tools by category."""
        return [
            t.metadata
            for t in self._tools.values()
            if t.metadata.category.value == category
        ]
