from __future__ import annotations

import base64
import logging
import time
from typing import Any
from uuid import uuid4

from backend.core.config import Settings
from backend.core.cost_tracker import CostTracker
from backend.core.media_asset import MediaAsset
from backend.core.openai_error_classification import classify_openai_error
from backend.core.openai_llm_provider import OpenAIProvider
from backend.core.provider_exceptions import PermanentProviderError
from backend.core.retry import retry_with_backoff
from backend.services.image_generation_provider import ImageGenerationProvider

logger = logging.getLogger(__name__)


class OpenAIImageGenerationProvider(ImageGenerationProvider):
    """Real OpenAI Images API-backed provider. Reuses the shared AsyncOpenAI client
    from `OpenAIProvider` — never creates a second client. Generated image bytes are
    embedded as a base64 data URI in `MediaAsset.source` so the interface stays a
    single `MediaAsset` return, unchanged for existing callers (ImageGenerationTool)."""

    def __init__(
        self,
        openai_llm_provider: OpenAIProvider,
        settings: Settings,
        cost_tracker: CostTracker | None = None,
    ) -> None:
        self._openai_llm_provider = openai_llm_provider
        self._settings = settings
        self._cost_tracker = cost_tracker or CostTracker()

    async def generate_image(
        self,
        *,
        prompt: str,
        size: str | None = None,
        quality: str | None = None,
        model: str | None = None,
        reference_image: bytes | None = None,
    ) -> MediaAsset:
        client = await self._openai_llm_provider.get_client()
        resolved_size = size or self._settings.openai_image_size
        resolved_quality = quality or self._settings.openai_image_quality
        resolved_model = model or self._settings.openai_image_model

        retry_count = 0
        used_reference = False

        def _record_attempt(attempt: int) -> None:
            nonlocal retry_count
            if attempt > 1:
                retry_count += 1

        async def _call_generate() -> Any:
            try:
                return await client.images.generate(
                    model=resolved_model,
                    prompt=prompt,
                    size=resolved_size,
                    quality=resolved_quality,
                    n=1,
                )
            except Exception as exc:
                raise classify_openai_error(exc) from exc

        async def _call_edit() -> Any:
            try:
                return await client.images.edit(
                    model=resolved_model,
                    image=("reference.png", reference_image, "image/png"),
                    prompt=prompt,
                    size=resolved_size,
                    quality=resolved_quality,
                    n=1,
                )
            except Exception as exc:
                raise classify_openai_error(exc) from exc

        started_at = time.perf_counter()
        if reference_image:
            # F31 Character Consistency: image-conditioned generation is a real
            # consistency upgrade over prompt text alone, but it is not the
            # baseline mechanism (see ImageGenerationProvider.generate_image's
            # docstring) — any failure here (unsupported model, malformed
            # reference, transient error) falls back to an ordinary text-to-image
            # call rather than failing the whole beat, exactly like every other
            # optional stage in this pipeline.
            try:
                response = await retry_with_backoff(_call_edit, on_attempt=_record_attempt)
                used_reference = True
            except Exception as exc:
                logger.warning("image_reference_edit_failed_falling_back_to_generate", extra={"reason": str(exc)})
                retry_count = 0
                response = await retry_with_backoff(_call_generate, on_attempt=_record_attempt)
        else:
            response = await retry_with_backoff(_call_generate, on_attempt=_record_attempt)
        duration_ms = (time.perf_counter() - started_at) * 1000
        b64_json = getattr(response.data[0], "b64_json", None)
        if not b64_json:
            raise PermanentProviderError("OpenAI image response did not include base64 image data")

        cost_estimate = self._cost_tracker.estimate_image_cost(
            provider="openai-image-generation", model=resolved_model, size=resolved_size, quality=resolved_quality
        )

        width, height = self._parse_size(resolved_size)
        return MediaAsset(
            id=str(uuid4()),
            type="image",
            source=f"data:image/png;base64,{b64_json}",
            provider="openai-image-generation",
            mime_type="image/png",
            width=width,
            height=height,
            prompt=prompt,
            metadata={
                "model": resolved_model,
                "quality": resolved_quality,
                "size": resolved_size,
                "generation_duration_ms": round(duration_ms, 2),
                "retry_count": retry_count,
                "estimated_cost_usd": cost_estimate.estimated_cost_usd,
                "used_reference_image": used_reference,
            },
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

    @staticmethod
    def decode_image_bytes(data_uri_source: str) -> bytes | None:
        """Decode the base64 payload embedded in a generated MediaAsset's `source`.
        Returns None for non-data-URI sources (e.g. placeholder provider output)."""
        prefix = "base64,"
        index = data_uri_source.find(prefix)
        if index == -1:
            return None
        try:
            return base64.b64decode(data_uri_source[index + len(prefix) :])
        except Exception:
            return None
