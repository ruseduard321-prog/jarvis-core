from __future__ import annotations

from uuid import uuid4

from backend.core.media_asset import MediaAsset
from backend.services.image_generation_provider import ImageGenerationProvider


class DefaultImageGenerationProvider(ImageGenerationProvider):
    """Default placeholder image generation provider for architecture validation."""

    async def generate_image(
        self,
        *,
        prompt: str,
        size: str | None = None,
        quality: str | None = None,
        model: str | None = None,
        reference_image: bytes | None = None,
    ) -> MediaAsset:
        width, height = self._parse_size(size)
        return MediaAsset(
            id=str(uuid4()),
            type="image",
            source="generated",
            provider="default-image-generation",
            mime_type="image/png",
            width=width,
            height=height,
            prompt=prompt,
            metadata={"placeholder": True, "size": size or "1024x1024", "quality": quality, "model": model},
        )

    def _parse_size(self, size: str | None) -> tuple[int, int]:
        raw = (size or "1024x1024").lower().strip()
        if "x" not in raw:
            return 1024, 1024
        left, right = raw.split("x", 1)
        try:
            return int(left), int(right)
        except ValueError:
            return 1024, 1024
