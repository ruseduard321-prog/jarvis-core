from __future__ import annotations

from typing import Any

from backend.core.tool import Tool
from backend.core.tool_models import ToolContext, ToolResult
from backend.services.image_generation_provider import ImageGenerationProvider


class ImageGenerationTool(Tool):
    """Generates images from prompts and returns normalized media assets."""

    def __init__(self, image_generation_provider: ImageGenerationProvider) -> None:
        self._image_generation_provider = image_generation_provider

    @property
    def slug(self) -> str:
        return "image-generation"

    @property
    def name(self) -> str:
        return "Image Generation Tool"

    @property
    def description(self) -> str:
        return "Generate an image from a prompt and return normalized media metadata."

    @property
    def capabilities(self) -> list[str]:
        return ["image.generate"]

    async def execute(self, args: dict[str, Any], context: ToolContext) -> ToolResult:
        prompt = str(args.get("prompt", "")).strip()
        if not prompt:
            return ToolResult(success=False, error="Missing required argument: prompt")

        size = str(args.get("size", "")).strip() or None
        asset = await self._image_generation_provider.generate_image(prompt=prompt, size=size)
        return ToolResult(
            success=True,
            output={"asset": asset.to_dict()},
            metadata={"tool_slug": self.slug, "capability": "image.generate"},
        )
