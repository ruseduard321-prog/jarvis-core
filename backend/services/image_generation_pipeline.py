from __future__ import annotations

import logging
from dataclasses import dataclass

from backend.core.cost_tracker import BudgetTracker, CostTracker
from backend.core.media_asset import MediaAsset
from backend.core.provider_exceptions import PermanentProviderError, ProviderError, TransientProviderError
from backend.services.image_generation_provider import ImageGenerationProvider
from backend.services.image_validation_service import ImageValidationResult, ImageValidationService
from backend.services.openai_image_generation_provider import OpenAIImageGenerationProvider

logger = logging.getLogger(__name__)

REGENERATION_HINT = (
    " Generate exactly ONE coherent photograph — no panels, no split-screen, no grid layout, no "
    "on-image text unless explicitly requested, anatomically correct figures."
)


class ImageBudgetExceededError(Exception):
    """Raised when the very first generation attempt is not affordable within the
    remaining production budget. Nothing was attempted and nothing was spent —
    callers should treat this as a graceful skip (F3), never a FAILED asset."""


class ImageGenerationFailedError(Exception):
    """Raised when the very first generation attempt is attempted but fails outright
    (provider error or undecodable response) — callers already have FAILED-asset
    handling for this case, unchanged from pre-F31.5 behavior."""


@dataclass
class GeneratedImage:
    """One accepted image, plus every real dollar it cost across generation,
    validation, and any regeneration — the single source of truth callers report
    as `estimated_cost_usd` on their own asset, so per-step cost aggregation
    (`context.cost_ledger`) reflects true total spend, not just the winning
    attempt's cost (F3)."""

    image_bytes: bytes
    media_asset: MediaAsset
    validation: ImageValidationResult
    total_cost_usd: float


class ImageGenerationPipeline:
    """F31.5: the one shared generate -> validate -> (maybe) regenerate flow,
    budget-enforced at every paid call. Previously `SceneImageGenerationService`
    and `ThumbnailGenerationService` each reimplemented an equivalent
    validate-and-regenerate loop independently (duplicated logic flagged in the
    F31 architecture review); `CharacterReferenceImageService` needed the same
    loop for F9. This class is the single implementation all three now use.

    Deliberately policy-free about what to do with a still-invalid result after
    retries are exhausted: it only ever decides HOW MANY attempts to make and
    WHETHER each one is affordable. Callers decide whether to ship an imperfect
    result (scene/thumbnail images always have to be *something*) or reject it
    outright (character reference portraits, per F9, must never accept an
    invalid identity anchor) — that policy difference lives entirely in the
    caller, not here."""

    def __init__(
        self,
        provider: ImageGenerationProvider,
        validation_service: ImageValidationService | None,
        cost_tracker: CostTracker | None = None,
    ) -> None:
        self._provider = provider
        self._validation_service = validation_service
        self._cost_tracker = cost_tracker or CostTracker()

    async def run(
        self,
        *,
        prompt: str,
        size: str,
        quality: str,
        model: str,
        budget: BudgetTracker,
        max_retries: int,
        reference_image: bytes | None = None,
        validation_context: str = "",
    ) -> GeneratedImage:
        """Raises ImageBudgetExceededError or ImageGenerationFailedError if the
        very first attempt never produces an image. Once a first image exists,
        this always returns a GeneratedImage — a failed/unaffordable regeneration
        attempt just means the original (possibly still-invalid) result is kept
        and returned, never an exception."""
        image_bytes, media_asset, total_cost = await self._attempt(
            prompt=prompt, size=size, quality=quality, model=model, reference_image=reference_image, budget=budget
        )

        validation, validation_cost = await self._validate(image_bytes, validation_context, budget)
        total_cost += validation_cost

        retries_left = max(0, max_retries)
        while not validation.valid and retries_left > 0:
            retries_left -= 1
            estimated_retry_cost = self._estimate_generation_cost(model=model, size=size, quality=quality)
            if not budget.can_afford(estimated_retry_cost):
                logger.info(
                    "image_regeneration_skipped_budget_exhausted",
                    extra={"estimated_cost_usd": estimated_retry_cost, "remaining_usd": budget.remaining_usd},
                )
                break  # keep the current (still-invalid) result — can't afford a retry

            logger.info("image_regeneration_triggered", extra={"issues": validation.issues, "reason": validation.reason})
            try:
                retry_bytes, retry_asset, retry_cost = await self._attempt(
                    prompt=f"{prompt}{REGENERATION_HINT}",
                    size=size,
                    quality=quality,
                    model=model,
                    reference_image=reference_image,
                    budget=budget,
                )
            except (ImageBudgetExceededError, ImageGenerationFailedError) as exc:
                logger.warning("image_regeneration_attempt_failed", extra={"reason": str(exc)})
                break  # regeneration attempt itself failed — keep the current result

            total_cost += retry_cost
            retry_validation, retry_validation_cost = await self._validate(retry_bytes, validation_context, budget)
            total_cost += retry_validation_cost
            image_bytes, media_asset, validation = retry_bytes, retry_asset, retry_validation

        return GeneratedImage(image_bytes=image_bytes, media_asset=media_asset, validation=validation, total_cost_usd=total_cost)

    def _estimate_generation_cost(self, *, model: str, size: str, quality: str) -> float:
        return self._cost_tracker.estimate_image_cost(
            provider="openai-image-generation", model=model, size=size, quality=quality
        ).estimated_cost_usd

    async def _attempt(
        self,
        *,
        prompt: str,
        size: str,
        quality: str,
        model: str,
        reference_image: bytes | None,
        budget: BudgetTracker,
    ) -> tuple[bytes, MediaAsset, float]:
        estimated_cost = self._estimate_generation_cost(model=model, size=size, quality=quality)
        if not budget.can_afford(estimated_cost):
            raise ImageBudgetExceededError(
                f"Estimated cost ${estimated_cost:.4f} exceeds remaining budget ${budget.remaining_usd:.4f}"
            )

        try:
            media_asset = await self._provider.generate_image(
                prompt=prompt, size=size, quality=quality, model=model, reference_image=reference_image
            )
        except (PermanentProviderError, TransientProviderError, ProviderError) as exc:
            raise ImageGenerationFailedError(str(exc)) from exc
        except Exception as exc:  # pragma: no cover - defensive path
            logger.exception("image_generation_attempt_unexpected_failure")
            raise ImageGenerationFailedError(f"Unexpected image generation failure: {exc}") from exc

        image_bytes = OpenAIImageGenerationProvider.decode_image_bytes(media_asset.source)
        if image_bytes is None:
            raise ImageGenerationFailedError("Image provider did not return decodable image data")

        actual_cost = float(media_asset.metadata.get("estimated_cost_usd", estimated_cost))
        budget.record_spend(actual_cost)
        return image_bytes, media_asset, actual_cost

    async def _validate(
        self, image_bytes: bytes, context: str, budget: BudgetTracker
    ) -> tuple[ImageValidationResult, float]:
        if self._validation_service is None:
            return ImageValidationResult(valid=True, reason="validation_disabled"), 0.0
        result = await self._validation_service.validate(image_bytes=image_bytes, context=context, budget_tracker=budget)
        return result, result.estimated_cost_usd
