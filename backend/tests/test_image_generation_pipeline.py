from __future__ import annotations

import base64

import pytest

from backend.core.cost_tracker import BudgetTracker
from backend.core.media_asset import MediaAsset
from backend.core.provider_exceptions import TransientProviderError
from backend.services.image_generation_pipeline import (
    ImageBudgetExceededError,
    ImageGenerationFailedError,
    ImageGenerationPipeline,
)
from backend.services.image_validation_service import ImageValidationResult


class FakeImageProvider:
    def __init__(self, *, media_assets: list[MediaAsset] | None = None, raises: Exception | None = None):
        self._media_assets = media_assets or []
        self._raises = raises
        self.calls: list[str] = []

    async def generate_image(self, *, prompt, size=None, quality=None, model=None, reference_image=None):
        self.calls.append(prompt)
        if self._raises:
            raise self._raises
        return self._media_assets[len(self.calls) - 1]


class FakeValidationService:
    def __init__(self, results: list[ImageValidationResult]):
        self._results = results
        self.calls = 0

    async def validate(self, *, image_bytes, context="", budget_tracker=None):
        result = self._results[self.calls]
        self.calls += 1
        if budget_tracker is not None:
            budget_tracker.record_spend(result.estimated_cost_usd)
        return result


def _data_uri(raw: bytes) -> str:
    return f"data:image/png;base64,{base64.b64encode(raw).decode('ascii')}"


def _media_asset(raw: bytes, cost: float = 0.063) -> MediaAsset:
    return MediaAsset(
        id="asset-1", type="image", source=_data_uri(raw), provider="openai-image-generation",
        mime_type="image/png", width=1536, height=1024, prompt="x",
        metadata={"model": "gpt-image-1", "retry_count": 0, "estimated_cost_usd": cost},
    )


@pytest.mark.asyncio
async def test_run_returns_first_image_when_no_validator_wired():
    provider = FakeImageProvider(media_assets=[_media_asset(b"raw-1")])
    pipeline = ImageGenerationPipeline(provider=provider, validation_service=None)
    budget = BudgetTracker(remaining_usd=5.0)

    result = await pipeline.run(prompt="a king", size="1536x1024", quality="medium", model="gpt-image-1", budget=budget, max_retries=1)

    assert result.image_bytes == b"raw-1"
    assert result.validation.valid is True
    assert result.validation.reason == "validation_disabled"
    assert result.total_cost_usd == 0.063
    assert len(provider.calls) == 1


@pytest.mark.asyncio
async def test_run_records_spend_on_the_shared_budget_tracker():
    provider = FakeImageProvider(media_assets=[_media_asset(b"raw-1", cost=0.063)])
    pipeline = ImageGenerationPipeline(provider=provider, validation_service=None)
    budget = BudgetTracker(remaining_usd=5.0)

    await pipeline.run(prompt="a king", size="1536x1024", quality="medium", model="gpt-image-1", budget=budget, max_retries=1)

    assert budget.remaining_usd == pytest.approx(5.0 - 0.063)


@pytest.mark.asyncio
async def test_run_raises_budget_exceeded_without_calling_the_provider():
    provider = FakeImageProvider(media_assets=[_media_asset(b"raw-1")])
    pipeline = ImageGenerationPipeline(provider=provider, validation_service=None)
    budget = BudgetTracker(remaining_usd=0.01)  # cheaper than the $0.063 estimate

    with pytest.raises(ImageBudgetExceededError):
        await pipeline.run(prompt="a king", size="1536x1024", quality="medium", model="gpt-image-1", budget=budget, max_retries=1)

    assert provider.calls == []  # never attempted, nothing spent


@pytest.mark.asyncio
async def test_run_raises_generation_failed_on_provider_error():
    provider = FakeImageProvider(raises=TransientProviderError("rate limited"))
    pipeline = ImageGenerationPipeline(provider=provider, validation_service=None)
    budget = BudgetTracker(remaining_usd=5.0)

    with pytest.raises(ImageGenerationFailedError):
        await pipeline.run(prompt="a king", size="1536x1024", quality="medium", model="gpt-image-1", budget=budget, max_retries=1)


@pytest.mark.asyncio
async def test_run_raises_generation_failed_on_undecodable_response():
    bad_asset = MediaAsset(
        id="a", type="image", source="generated", provider="openai-image-generation", mime_type="image/png",
        metadata={},
    )
    provider = FakeImageProvider(media_assets=[bad_asset])
    pipeline = ImageGenerationPipeline(provider=provider, validation_service=None)
    budget = BudgetTracker(remaining_usd=5.0)

    with pytest.raises(ImageGenerationFailedError):
        await pipeline.run(prompt="a king", size="1536x1024", quality="medium", model="gpt-image-1", budget=budget, max_retries=1)


@pytest.mark.asyncio
async def test_run_regenerates_once_when_first_attempt_is_invalid():
    provider = FakeImageProvider(media_assets=[_media_asset(b"raw-1"), _media_asset(b"raw-2")])
    validator = FakeValidationService(
        [
            ImageValidationResult(valid=False, issues=["multi-panel"], reason="split into panels", estimated_cost_usd=0.01),
            ImageValidationResult(valid=True, estimated_cost_usd=0.01),
        ]
    )
    pipeline = ImageGenerationPipeline(provider=provider, validation_service=validator)
    budget = BudgetTracker(remaining_usd=5.0)

    result = await pipeline.run(prompt="a king", size="1536x1024", quality="medium", model="gpt-image-1", budget=budget, max_retries=1)

    assert result.image_bytes == b"raw-2"
    assert result.validation.valid is True
    assert len(provider.calls) == 2
    assert provider.calls[1].startswith("a king")
    assert provider.calls[1] != provider.calls[0]  # the retry prompt carries the regeneration hint
    assert result.total_cost_usd == pytest.approx(0.063 + 0.01 + 0.063 + 0.01)


@pytest.mark.asyncio
async def test_run_keeps_original_result_when_still_invalid_after_retries_exhausted():
    provider = FakeImageProvider(media_assets=[_media_asset(b"raw-1"), _media_asset(b"raw-2")])
    validator = FakeValidationService(
        [
            ImageValidationResult(valid=False, issues=["multi-panel"], estimated_cost_usd=0.01),
            ImageValidationResult(valid=False, issues=["still broken"], estimated_cost_usd=0.01),
        ]
    )
    pipeline = ImageGenerationPipeline(provider=provider, validation_service=validator)
    budget = BudgetTracker(remaining_usd=5.0)

    result = await pipeline.run(prompt="a king", size="1536x1024", quality="medium", model="gpt-image-1", budget=budget, max_retries=1)

    # Two attempts were made (max_retries=1); the final (still-invalid) one is returned.
    assert result.image_bytes == b"raw-2"
    assert result.validation.valid is False
    assert len(provider.calls) == 2


@pytest.mark.asyncio
async def test_run_stops_retrying_once_max_retries_exhausted():
    provider = FakeImageProvider(media_assets=[_media_asset(b"raw-1")])
    validator = FakeValidationService([ImageValidationResult(valid=False, issues=["broken"], estimated_cost_usd=0.01)])
    pipeline = ImageGenerationPipeline(provider=provider, validation_service=validator)
    budget = BudgetTracker(remaining_usd=5.0)

    result = await pipeline.run(prompt="a king", size="1536x1024", quality="medium", model="gpt-image-1", budget=budget, max_retries=0)

    assert len(provider.calls) == 1
    assert result.validation.valid is False


@pytest.mark.asyncio
async def test_run_skips_regeneration_when_budget_cannot_afford_a_retry():
    provider = FakeImageProvider(media_assets=[_media_asset(b"raw-1", cost=0.063)])
    validator = FakeValidationService([ImageValidationResult(valid=False, issues=["broken"], estimated_cost_usd=0.0)])
    pipeline = ImageGenerationPipeline(provider=provider, validation_service=validator)
    # Enough for exactly one generation, nothing left for a second.
    budget = BudgetTracker(remaining_usd=0.063)

    result = await pipeline.run(prompt="a king", size="1536x1024", quality="medium", model="gpt-image-1", budget=budget, max_retries=1)

    assert len(provider.calls) == 1
    assert result.validation.valid is False


@pytest.mark.asyncio
async def test_run_passes_reference_image_through_to_the_provider():
    captured = {}

    class CapturingProvider(FakeImageProvider):
        async def generate_image(self, *, prompt, size=None, quality=None, model=None, reference_image=None):
            captured["reference_image"] = reference_image
            return await super().generate_image(prompt=prompt, size=size, quality=quality, model=model, reference_image=reference_image)

    provider = CapturingProvider(media_assets=[_media_asset(b"raw-1")])
    pipeline = ImageGenerationPipeline(provider=provider, validation_service=None)
    budget = BudgetTracker(remaining_usd=5.0)

    await pipeline.run(
        prompt="a king", size="1536x1024", quality="medium", model="gpt-image-1",
        reference_image=b"ref-bytes", budget=budget, max_retries=1,
    )

    assert captured["reference_image"] == b"ref-bytes"
