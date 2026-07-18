from __future__ import annotations

import asyncio
import time
from typing import Any

from backend.core.event_bus_service import EventBusService
from backend.core.tool import Tool, ToolRegistry
from backend.core.tool_models import ToolContext, ToolResult


class ToolExecutor:
    """Service for executing tools with validation, timeout, and event tracking."""

    def __init__(self, tool_registry: ToolRegistry, event_bus_service: EventBusService) -> None:
        self._tool_registry = tool_registry
        self._event_bus_service = event_bus_service

    async def execute(
        self,
        tool_name: str,
        args: dict[str, Any],
        context: ToolContext,
    ) -> ToolResult:
        """Execute a tool with validation and timeout."""
        try:
            tool = self._tool_registry.get(tool_name)
        except ValueError as e:
            result = ToolResult(success=False, error=str(e))
            await self._event_bus_service.publish_event(
                "ToolFailed",
                payload={"tool_name": tool_name, "error": str(e)},
                metadata={"tool_name": tool_name},
            )
            return result

        if not tool.metadata.enabled:
            error = f"Tool disabled: {tool_name}"
            result = ToolResult(success=False, error=error)
            await self._event_bus_service.publish_event(
                "ToolFailed",
                payload={"tool_name": tool_name, "error": error},
                metadata={"tool_name": tool_name},
            )
            return result

        # Validate arguments
        validation_error = self._validate_arguments(tool, args)
        if validation_error:
            result = ToolResult(success=False, error=validation_error)
            await self._event_bus_service.publish_event(
                "ToolFailed",
                payload={"tool_name": tool_name, "error": validation_error},
                metadata={"tool_name": tool_name},
            )
            return result

        # Execute with timeout
        start_time = time.time()
        try:
            if tool.metadata.timeout_seconds:
                result = await asyncio.wait_for(
                    tool.execute(args, context),
                    timeout=tool.metadata.timeout_seconds,
                )
            else:
                result = await tool.execute(args, context)

            execution_time_ms = int((time.time() - start_time) * 1000)
            result = ToolResult(
                success=result.success,
                output=result.output,
                error=result.error,
                execution_time_ms=execution_time_ms,
                metadata=result.metadata,
            )

            await self._event_bus_service.publish_event(
                "ToolExecuted",
                payload={
                    "tool_name": tool_name,
                    "success": result.success,
                    "execution_time_ms": execution_time_ms,
                },
                metadata={"tool_name": tool_name},
            )

            return result

        except asyncio.TimeoutError:
            error = f"Tool timeout after {tool.metadata.timeout_seconds}s: {tool_name}"
            result = ToolResult(success=False, error=error)
            await self._event_bus_service.publish_event(
                "ToolFailed",
                payload={"tool_name": tool_name, "error": error},
                metadata={"tool_name": tool_name},
            )
            return result
        except Exception as e:
            error = f"Tool execution error: {str(e)}"
            result = ToolResult(success=False, error=error)
            await self._event_bus_service.publish_event(
                "ToolFailed",
                payload={"tool_name": tool_name, "error": error},
                metadata={"tool_name": tool_name},
            )
            return result

    def _validate_arguments(self, tool: Tool, args: dict[str, Any]) -> str | None:
        """Validate tool arguments against metadata."""
        for param in tool.metadata.parameters:
            if param.required and param.name not in args:
                return f"Missing required parameter: {param.name}"
            if param.name in args and param.enum_values:
                if args[param.name] not in param.enum_values:
                    return f"Invalid value for {param.name}: {args[param.name]}"
        return None
