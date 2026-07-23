from __future__ import annotations

import time
from typing import Any

from backend.core.event_bus_service import EventBusService
from backend.core.tool import ToolRegistry
from backend.core.tool_models import ToolContext, ToolResult


class ToolManager:
    """Centralized tool execution façade for runtime and future concerns."""

    def __init__(self, tool_registry: ToolRegistry, event_bus_service: EventBusService) -> None:
        self._tool_registry = tool_registry
        self._event_bus_service = event_bus_service

    async def execute(
        self,
        tool_slug: str,
        args: dict[str, Any],
        context: ToolContext,
    ) -> ToolResult:
        """Validate tool existence, execute, and normalize the resulting payload."""
        try:
            tool = self._tool_registry.get(tool_slug)
        except ValueError as error:
            result = ToolResult(success=False, error=str(error), metadata={"tool_slug": tool_slug})
            await self._event_bus_service.publish_event(
                "ToolFailed",
                payload={"tool_slug": tool_slug, "error": str(error)},
                metadata={"tool_slug": tool_slug},
            )
            return result

        start_time = time.time()
        try:
            result = await tool.execute(args, context)
            elapsed_ms = int((time.time() - start_time) * 1000)
            normalized_result = ToolResult(
                success=result.success,
                output=result.output,
                error=result.error,
                metadata={**result.metadata, "tool_slug": tool_slug, "duration_ms": elapsed_ms},
            )
            await self._event_bus_service.publish_event(
                "ToolExecuted",
                payload={"tool_slug": tool_slug, "success": normalized_result.success, "duration_ms": elapsed_ms},
                metadata={"tool_slug": tool_slug},
            )
            return normalized_result
        except Exception as error:
            failure = ToolResult(
                success=False,
                error=f"Tool execution error: {error}",
                metadata={"tool_slug": tool_slug},
            )
            await self._event_bus_service.publish_event(
                "ToolFailed",
                payload={"tool_slug": tool_slug, "error": str(error)},
                metadata={"tool_slug": tool_slug},
            )
            return failure
