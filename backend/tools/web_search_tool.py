from __future__ import annotations

from typing import Any

from backend.core.tool import Tool
from backend.core.tool_models import ToolContext, ToolResult
from backend.services.search_provider import SearchProvider


class WebSearchTool(Tool):
    """Searches the web and returns structured result entries."""

    def __init__(self, search_provider: SearchProvider) -> None:
        self._search_provider = search_provider

    @property
    def slug(self) -> str:
        return "web-search"

    @property
    def name(self) -> str:
        return "Web Search Tool"

    @property
    def description(self) -> str:
        return "Search the web and return structured results with title, url, snippet, and source."

    @property
    def capabilities(self) -> list[str]:
        return ["web.search"]

    async def execute(self, args: dict[str, Any], context: ToolContext) -> ToolResult:
        query = str(args.get("query", "")).strip()
        if not query:
            return ToolResult(success=False, error="Missing required argument: query")

        try:
            limit = int(args.get("limit", 8))
        except (TypeError, ValueError):
            return ToolResult(success=False, error="Invalid argument: limit must be an integer")

        limit = max(1, min(limit, 20))

        results = await self._search_provider.search(query=query, limit=limit)
        return ToolResult(
            success=True,
            output={
                "query": query,
                "results": results,
                "count": len(results),
            },
            metadata={"tool_slug": self.slug, "capability": "web.search"},
        )
