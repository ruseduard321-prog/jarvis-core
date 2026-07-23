from __future__ import annotations

import logging
import re

from backend.core.config import Settings
from backend.core.cost_tracker import CostTracker
from backend.schemas.visual_identity import CharacterVisualIdentity, HistoricalVisualContext
from backend.services.image_generation_pipeline import (
    ImageBudgetExceededError,
    ImageGenerationFailedError,
    ImageGenerationPipeline,
)
from backend.services.image_generation_provider import ImageGenerationProvider
from backend.services.image_validation_service import ImageValidationService

logger = logging.getLogger(__name__)

# Reference portraits are a clean single-subject anchor, not a cinematic frame —
# a square crop keeps the whole figure/face centered without the wasted
# left/right margin a landscape canvas would add for a single standing subject.
_REFERENCE_IMAGE_SIZE = "1024x1024"

_SLUG_PATTERN = re.compile(r"[^a-z0-9]+")


def _slug(name: str) -> str:
    slug = _SLUG_PATTERN.sub("_", name.lower()).strip("_")
    return slug or "figure"


class CharacterReferenceImageService:
    """F31 Character Consistency: generates one canonical reference portrait per
    recurring figure identified by VisualIdentityService. The portrait is the
    stronger, provider-optional consistency anchor (see
    ImageGenerationProvider.generate_image's `reference_image` parameter) that later
    scene/thumbnail generations can be conditioned on when a provider supports it;
    the character's text description (CharacterVisualIdentity.as_prompt_fragment())
    remains the baseline, provider-agnostic mechanism regardless of whether this
    step succeeds. Never raises — a rejected or failed portrait simply leaves that
    character's reference_image_filename empty, and downstream generation falls
    back to text-only consistency for that figure.

    F9 (F31.5 hardening): every generated portrait is validated through
    ImageValidationService before acceptance, via the shared, budget-aware
    ImageGenerationPipeline (one retry on failure, matching every other image QA
    gate in this pipeline). A portrait that is STILL invalid after that retry is
    never accepted as the identity anchor — this is the one place in the pipeline
    where an invalid image must never ship, because every subsequent scene
    depicting that character inherits whatever this portrait gets wrong."""

    def __init__(
        self,
        image_generation_provider: ImageGenerationProvider,
        settings: Settings,
        image_validation_service: ImageValidationService | None = None,
    ) -> None:
        self._settings = settings
        self._cost_tracker = CostTracker()
        self._pipeline = ImageGenerationPipeline(
            provider=image_generation_provider, validation_service=image_validation_service, cost_tracker=self._cost_tracker
        )

    async def execute(
        self,
        *,
        characters: list[CharacterVisualIdentity],
        historical_context: HistoricalVisualContext | None = None,
        estimated_cost_so_far_usd: float = 0.0,
    ) -> tuple[list[CharacterVisualIdentity], dict[str, bytes], float]:
        if not characters or not self._settings.character_reference_images_enabled:
            return list(characters), {}, 0.0

        budget = self._cost_tracker.build_budget_tracker(
            maximum_budget_usd=self._settings.maximum_video_budget_usd,
            estimated_cost_so_far_usd=estimated_cost_so_far_usd,
        )

        updated: list[CharacterVisualIdentity] = []
        image_bytes_by_filename: dict[str, bytes] = {}
        total_cost_usd = 0.0

        for index, character in enumerate(characters, start=1):
            filename = f"character_{index:02d}_{_slug(character.name)}.png"
            prompt = character.reference_portrait_prompt(historical_context)

            try:
                result = await self._pipeline.run(
                    prompt=prompt,
                    size=_REFERENCE_IMAGE_SIZE,
                    quality=self._settings.openai_image_quality,
                    model=self._settings.openai_image_model,
                    budget=budget,
                    max_retries=self._settings.image_validation_max_retries,
                    validation_context=f"Reference portrait of {character.name}",
                )
            except ImageBudgetExceededError as exc:
                logger.warning("character_reference_image_skipped_budget_exhausted", extra={"character": character.name, "reason": str(exc)})
                updated.append(character)
                continue
            except ImageGenerationFailedError as exc:
                logger.warning("character_reference_image_failed", extra={"character": character.name, "reason": str(exc)})
                updated.append(character)
                continue

            total_cost_usd += result.total_cost_usd

            if not result.validation.valid:
                # F9: never allow an invalid reference portrait to become this
                # character's identity anchor — leave reference_image_filename
                # empty so downstream generation falls back to text-only
                # consistency for this figure instead of propagating a broken
                # image into every scene that depicts them.
                logger.warning(
                    "character_reference_image_rejected_after_validation",
                    extra={"character": character.name, "issues": result.validation.issues, "reason": result.validation.reason},
                )
                updated.append(character)
                continue

            updated.append(character.model_copy(update={"reference_image_filename": filename}))
            image_bytes_by_filename[filename] = result.image_bytes

        return updated, image_bytes_by_filename, round(total_cost_usd, 6)
