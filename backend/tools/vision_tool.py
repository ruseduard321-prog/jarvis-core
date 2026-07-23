from __future__ import annotations

from typing import Any

from backend.core.tool import Tool
from backend.core.tool_models import ToolContext, ToolResult
from backend.services.vision_provider import VisionProvider


class VisionTool(Tool):
    """Analyzes images and returns structured observations."""

    def __init__(self, vision_provider: VisionProvider) -> None:
        self._vision_provider = vision_provider

    @property
    def slug(self) -> str:
        return "vision"

    @property
    def name(self) -> str:
        return "Vision Tool"

    @property
    def description(self) -> str:
        return "Analyze an image and return structured observations."

    @property
    def capabilities(self) -> list[str]:
        return ["image.analyze"]

    async def execute(self, args: dict[str, Any], context: ToolContext) -> ToolResult:
        source = (
            str(args.get("source", "")).strip()
            or str(args.get("url", "")).strip()
            or str(args.get("image_url", "")).strip()
            or str(args.get("path", "")).strip()
        )
        if not source:
            return ToolResult(success=False, error="Missing required argument: source|url|image_url|path")

        prompt = str(args.get("prompt", "")).strip() or None
        asset, observations = await self._vision_provider.analyze_image(source=source, prompt=prompt)
        return ToolResult(
            success=True,
            output={
                "asset": asset.to_dict(),
                "observations": observations,
            },
            metadata={"tool_slug": self.slug, "capability": "image.analyze"},
        )
