from __future__ import annotations

from abc import ABC, abstractmethod

from backend.core.media_asset import MediaAsset


class ImageGenerationProvider(ABC):
    """Provider abstraction for image generation services."""

    @abstractmethod
    async def generate_image(
        self,
        *,
        prompt: str,
        size: str | None = None,
        quality: str | None = None,
        model: str | None = None,
        reference_image: bytes | None = None,
    ) -> MediaAsset:
        """Generate one image from `prompt`. `reference_image`, when given, is a
        provider-agnostic hint (F31 Character Consistency): a provider MAY use it to
        condition generation on a reference likeness (e.g. an image-edit/img2img call)
        for stronger consistency than prompt text alone; a provider that has no such
        capability MUST simply ignore it and generate from `prompt` as usual. Callers
        must never depend on the reference actually being honored — the prompt text
        alone (via CharacterVisualIdentity.as_prompt_fragment()) is always the
        baseline consistency mechanism."""
        raise NotImplementedError
