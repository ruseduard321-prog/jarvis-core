from __future__ import annotations

from typing import Any

from backend.core.tool import Tool
from backend.core.tool_models import ToolContext, ToolResult
from backend.services.tool_content_processing_service import ToolContentProcessingService
from backend.services.tool_resource_loader_service import ToolResourceLoaderService


class URLReaderTool(Tool):
    """Fetches a webpage and extracts readable content with metadata."""

    def __init__(
        self,
        resource_loader: ToolResourceLoaderService,
        content_processor: ToolContentProcessingService,
    ) -> None:
        self._resource_loader = resource_loader
        self._content_processor = content_processor

    @property
    def slug(self) -> str:
        return "url-reader"

    @property
    def name(self) -> str:
        return "URL Reader Tool"

    @property
    def description(self) -> str:
        return "Fetch a webpage, clean non-content sections, and return readable text with metadata."

    @property
    def capabilities(self) -> list[str]:
        return ["url.read"]

    async def execute(self, args: dict[str, Any], context: ToolContext) -> ToolResult:
        url = str(args.get("url", "")).strip()
        if not url:
            return ToolResult(success=False, error="Missing required argument: url")

        html, load_meta = await self._resource_loader.load_text(url=url)
        html_meta = self._content_processor.extract_html_metadata(html, str(load_meta.get("url", url)))
        content = self._content_processor.clean_html_to_text(html)

        # Optional cap so a large real page (a full Wikipedia article can be tens of
        # thousands of characters) doesn't blow the LLM's context window when this
        # content is later relayed through an agent turn. Real callers that need the
        # full text can omit max_length.
        max_length = args.get("max_length")
        truncated = False
        if isinstance(max_length, int) and max_length > 0 and len(content) > max_length:
            content = content[:max_length]
            truncated = True

        document = self._content_processor.build_document(
            content=content,
            source_meta={**load_meta, **html_meta},
            title=html_meta.get("title") or None,
            language="text",
        )

        return ToolResult(
            success=True,
            output=document.to_dict(),
            metadata={"tool_slug": self.slug, "capability": "url.read", "truncated": truncated},
        )
