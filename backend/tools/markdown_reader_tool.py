from __future__ import annotations

from typing import Any

from backend.core.tool import Tool
from backend.core.tool_models import ToolContext, ToolResult
from backend.services.tool_content_processing_service import ToolContentProcessingService
from backend.services.tool_resource_loader_service import ToolResourceLoaderService


class MarkdownReaderTool(Tool):
    """Reads markdown content preserving headings, lists, and code blocks."""

    def __init__(
        self,
        resource_loader: ToolResourceLoaderService,
        content_processor: ToolContentProcessingService,
    ) -> None:
        self._resource_loader = resource_loader
        self._content_processor = content_processor

    @property
    def slug(self) -> str:
        return "markdown-reader"

    @property
    def name(self) -> str:
        return "Markdown Reader Tool"

    @property
    def description(self) -> str:
        return "Parse markdown and preserve structural blocks such as headings, lists, and code blocks."

    @property
    def capabilities(self) -> list[str]:
        return ["markdown.read"]

    async def execute(self, args: dict[str, Any], context: ToolContext) -> ToolResult:
        path = str(args.get("path", "")).strip() or None
        url = str(args.get("url", "")).strip() or None
        content = args.get("content")

        if content is not None:
            markdown_text = str(content)
            source_meta: dict[str, Any] = {"source": "inline"}
        else:
            if not path and not url:
                return ToolResult(success=False, error="Provide one of: content, path, url")
            markdown_text, source_meta = await self._resource_loader.load_text(path=path, url=url)

        structured = self._content_processor.parse_markdown_preserving_structure(markdown_text)
        document = self._content_processor.build_document(
            content=structured,
            source_meta=source_meta,
            language="markdown",
        )
        return ToolResult(
            success=True,
            output=document.to_dict(),
            metadata={"tool_slug": self.slug, "capability": "markdown.read"},
        )
