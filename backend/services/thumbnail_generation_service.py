from __future__ import annotations

import logging
from datetime import datetime, timezone

from backend.core.config import Settings
from backend.core.cost_tracker import CostTracker
from backend.schemas.assets import ImageAsset
from backend.schemas.composition import CameraIntent, ColorLanguage, CompositionStyle
from backend.schemas.visual_identity import VisualIdentityContext
from backend.services.image_generation_pipeline import (
    ImageBudgetExceededError,
    ImageGenerationFailedError,
    ImageGenerationPipeline,
)
from backend.services.image_generation_provider import ImageGenerationProvider
from backend.services.image_validation_service import ImageValidationService
from backend.services.photorealistic_prompt_builder import PhotorealisticPromptBuilder

logger = logging.getLogger(__name__)


class ThumbnailGenerationService:
    """Generates the production thumbnail image from the Media step's thumbnail prompt.
    Never raises — provider failures are captured as a FAILED ImageAsset so the
    workflow continues.

    F31 Thumbnail Consistency: the thumbnail is run through the same
    PhotorealisticPromptBuilder used for every scene/beat image, and, when a
    VisualIdentityContext is supplied, anchored to the same HistoricalVisualContext
    and canonical CharacterVisualIdentity as the body of the documentary.

    F31.5: generation, validation, and any regeneration run through the shared,
    budget-aware ImageGenerationPipeline — once the production's remaining budget
    is exhausted, the thumbnail is gracefully SKIPPED rather than generated
    regardless."""

    def __init__(
        self,
        image_generation_provider: ImageGenerationProvider,
        settings: Settings,
        image_validation_service: ImageValidationService | None = None,
        prompt_builder: PhotorealisticPromptBuilder | None = None,
    ) -> None:
        self._settings = settings
        self._prompt_builder = prompt_builder or PhotorealisticPromptBuilder()
        # Stateless — safe to own a private instance without adding a DI wire.
        self._cost_tracker = CostTracker()
        self._pipeline = ImageGenerationPipeline(
            provider=image_generation_provider, validation_service=image_validation_service, cost_tracker=self._cost_tracker
        )

    async def execute(
        self,
        thumbnail_prompt: str,
        *,
        visual_identity_context: VisualIdentityContext | None = None,
        reference_images: dict[str, bytes] | None = None,
        estimated_cost_so_far_usd: float = 0.0,
    ) -> tuple[ImageAsset, bytes | None]:
        # Cost protection (Part 2): this is (usually) the first image-generation call
        # in the whole production run, so the run's full image cost ceiling is logged
        # here, before any images.generate request is sent. The scene count used is
        # the app-enforced ceiling (max_scenes_per_video), not an LLM-reported
        # number — production cost must be deterministic and under application
        # control, not a surprise reconstructed from a bill after the fact.
        preview = self._cost_tracker.build_image_generation_preview(
            scene_count=self._settings.max_scenes_per_video,
            thumbnail_count=1,
            model=self._settings.openai_image_model,
            size=self._settings.openai_image_size,
            quality=self._settings.openai_image_quality,
        )
        logger.info(preview)

        raw_prompt = thumbnail_prompt.strip()
        if not raw_prompt:
            return self._skipped("No thumbnail prompt was produced by the Media step"), None

        character = visual_identity_context.character_for(raw_prompt) if visual_identity_context is not None else None
        historical_context = visual_identity_context.historical_context if visual_identity_context is not None else None
        prompt = self._prompt_builder.build(
            subject_and_action=raw_prompt,
            composition_style=CompositionStyle.CLOSE_UP,
            camera_intent=CameraIntent.EMOTIONAL_FOCUS,
            color_language=ColorLanguage.TENSION,
            mood="bold, eye-catching YouTube thumbnail — not clickbait, matches the documentary's own visual language",
            historical_context=historical_context,
            character=character,
        )
        reference_image = (
            (reference_images or {}).get(character.reference_image_filename)
            if character is not None and character.reference_image_filename
            else None
        )

        budget = self._cost_tracker.build_budget_tracker(
            maximum_budget_usd=self._settings.maximum_video_budget_usd,
            estimated_cost_so_far_usd=estimated_cost_so_far_usd,
        )

        try:
            result = await self._pipeline.run(
                prompt=prompt,
                size=self._settings.openai_image_size,
                quality=self._settings.openai_image_quality,
                model=self._settings.openai_image_model,
                reference_image=reference_image,
                budget=budget,
                max_retries=self._settings.image_validation_max_retries,
                validation_context=prompt,
            )
        except ImageBudgetExceededError as exc:
            logger.warning("thumbnail_generation_skipped_budget_exhausted", extra={"reason": str(exc)})
            return self._skipped(f"Skipped: production budget exhausted ({exc})"), None
        except ImageGenerationFailedError as exc:
            logger.warning("thumbnail_generation_failed", extra={"reason": str(exc)})
            return self._failed(str(exc)), None

        media_asset = result.media_asset
        resolution = f"{media_asset.width}x{media_asset.height}" if media_asset.width and media_asset.height else ""
        asset = ImageAsset(
            provider=media_asset.provider,
            model=str(media_asset.metadata.get("model", "")),
            resolution=resolution,
            prompt=prompt,
            generation_time=datetime.now(timezone.utc).isoformat(),
            status="SUCCESS",
            generation_duration_ms=float(media_asset.metadata.get("generation_duration_ms", 0.0)),
            retry_count=int(media_asset.metadata.get("retry_count", 0)),
            estimated_cost_usd=result.total_cost_usd,
            validation_status="valid" if result.validation.valid else "invalid",
            validation_issues=result.validation.issues,
        )
        return asset, result.image_bytes

    def _skipped(self, reason: str) -> ImageAsset:
        return ImageAsset(
            provider="none",
            generation_time=datetime.now(timezone.utc).isoformat(),
            status="SKIPPED",
            error=reason,
        )

    def _failed(self, reason: str) -> ImageAsset:
        return ImageAsset(
            provider="none",
            generation_time=datetime.now(timezone.utc).isoformat(),
            status="FAILED",
            error=reason,
        )
