from __future__ import annotations

from typing import Any

from backend.core.tool import Tool
from backend.core.tool_models import ToolContext, ToolResult
from backend.services.tool_content_processing_service import ToolContentProcessingService
from backend.services.tool_resource_loader_service import ToolResourceLoaderService


class PDFReaderTool(Tool):
    """Reads PDF files, preserving page order in extracted output."""

    def __init__(
        self,
        resource_loader: ToolResourceLoaderService,
        content_processor: ToolContentProcessingService,
    ) -> None:
        self._resource_loader = resource_loader
        self._content_processor = content_processor

    @property
    def slug(self) -> str:
        return "pdf-reader"

    @property
    def name(self) -> str:
        return "PDF Reader Tool"

    @property
    def description(self) -> str:
        return "Extract text from PDF while preserving page order and readable section boundaries."

    @property
    def capabilities(self) -> list[str]:
        return ["pdf.read"]

    async def execute(self, args: dict[str, Any], context: ToolContext) -> ToolResult:
        path = str(args.get("path", "")).strip() or None
        url = str(args.get("url", "")).strip() or None
        if not path and not url:
            return ToolResult(success=False, error="Provide either 'path' or 'url'.")

        raw, source_meta = await self._resource_loader.load_bytes(path=path, url=url)
        try:
            content, pdf_meta = self._content_processor.extract_pdf_text(raw)
        except RuntimeError as exc:
            return ToolResult(success=False, error=str(exc))

        document = self._content_processor.build_document(
            content=content,
            source_meta={**source_meta, **pdf_meta},
            language="pdf",
        )
        return ToolResult(
            success=True,
            output=document.to_dict(),
            metadata={"tool_slug": self.slug, "capability": "pdf.read"},
        )
