from __future__ import annotations

from typing import Any

from backend.core.tool import Tool
from backend.core.tool_models import ToolContext, ToolResult
from backend.services.tool_content_processing_service import ToolContentProcessingService
from backend.services.tool_resource_loader_service import ToolResourceLoaderService


class TextReaderTool(Tool):
    """Reads plain text and normalizes encoding/newline conventions."""

    def __init__(
        self,
        resource_loader: ToolResourceLoaderService,
        content_processor: ToolContentProcessingService,
    ) -> None:
        self._resource_loader = resource_loader
        self._content_processor = content_processor

    @property
    def slug(self) -> str:
        return "text-reader"

    @property
    def name(self) -> str:
        return "Text Reader Tool"

    @property
    def description(self) -> str:
        return "Load plain text from file, URL, or inline content and normalize encoding safely."

    @property
    def capabilities(self) -> list[str]:
        return ["text.read"]

    async def execute(self, args: dict[str, Any], context: ToolContext) -> ToolResult:
        path = str(args.get("path", "")).strip() or None
        url = str(args.get("url", "")).strip() or None
        content = args.get("content")
        encoding = str(args.get("encoding", "")).strip() or None

        if content is not None:
            text = str(content)
            source_meta: dict[str, Any] = {"source": "inline"}
        else:
            if not path and not url:
                return ToolResult(success=False, error="Provide one of: content, path, url")
            text, source_meta = await self._resource_loader.load_text(path=path, url=url, encoding=encoding)

        normalized = self._content_processor.normalize_text(text)
        document = self._content_processor.build_document(
            content=normalized,
            source_meta=source_meta,
            language="text",
        )
        return ToolResult(
            success=True,
            output=document.to_dict(),
            metadata={"tool_slug": self.slug, "capability": "text.read"},
        )
