from __future__ import annotations

import base64

import pytest

from backend.core.config import Settings
from backend.core.media_asset import MediaAsset
from backend.core.provider_exceptions import TransientProviderError
from backend.schemas.visual_identity import CharacterVisualIdentity, HistoricalVisualContext
from backend.services.character_reference_image_service import CharacterReferenceImageService


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
    def __init__(self, results):
        self._results = results
        self.calls = 0

    async def validate(self, *, image_bytes, context="", budget_tracker=None):
        result = self._results[self.calls]
        self.calls += 1
        if budget_tracker is not None:
            budget_tracker.record_spend(result.estimated_cost_usd)
        return result


def _media_asset(source: str) -> MediaAsset:
    return MediaAsset(
        id="asset-1", type="image", source=source, provider="openai-image-generation",
        mime_type="image/png", width=1024, height=1024, prompt="a portrait",
        metadata={"model": "gpt-image-1", "estimated_cost_usd": 0.042},
    )


def _data_uri(raw: bytes) -> str:
    return f"data:image/png;base64,{base64.b64encode(raw).decode('ascii')}"


@pytest.mark.asyncio
async def test_execute_returns_unchanged_when_no_characters():
    service = CharacterReferenceImageService(image_generation_provider=FakeImageProvider(), settings=Settings())

    characters, images, cost = await service.execute(characters=[])

    assert characters == []
    assert images == {}
    assert cost == 0.0


@pytest.mark.asyncio
async def test_execute_generates_one_portrait_per_character_with_filename():
    raw = b"portrait-bytes"
    provider = FakeImageProvider(media_assets=[_media_asset(_data_uri(raw))])
    service = CharacterReferenceImageService(image_generation_provider=provider, settings=Settings())
    characters = [CharacterVisualIdentity(name="Mansa Musa")]

    updated, images, cost = await service.execute(characters=characters, historical_context=HistoricalVisualContext())

    assert updated[0].reference_image_filename == "character_01_mansa_musa.png"
    assert images[updated[0].reference_image_filename] == raw
    assert "Studio reference portrait of Mansa Musa" in provider.calls[0]
    assert cost == pytest.approx(0.042)


@pytest.mark.asyncio
async def test_execute_leaves_character_unchanged_on_provider_failure():
    provider = FakeImageProvider(raises=TransientProviderError("rate limited"))
    service = CharacterReferenceImageService(image_generation_provider=provider, settings=Settings())
    characters = [CharacterVisualIdentity(name="Mansa Musa")]

    updated, images, cost = await service.execute(characters=characters)

    assert updated[0].reference_image_filename == ""
    assert images == {}
    assert cost == 0.0


@pytest.mark.asyncio
async def test_execute_skips_entirely_when_disabled_by_settings():
    provider = FakeImageProvider(media_assets=[_media_asset(_data_uri(b"x"))])
    service = CharacterReferenceImageService(
        image_generation_provider=provider, settings=Settings(character_reference_images_enabled=False)
    )
    characters = [CharacterVisualIdentity(name="Mansa Musa")]

    updated, images, cost = await service.execute(characters=characters)

    assert updated == characters
    assert images == {}
    assert cost == 0.0
    assert provider.calls == []


@pytest.mark.asyncio
async def test_execute_generates_distinct_filenames_for_multiple_characters():
    raws = [b"a", b"b"]
    provider = FakeImageProvider(media_assets=[_media_asset(_data_uri(r)) for r in raws])
    service = CharacterReferenceImageService(image_generation_provider=provider, settings=Settings())
    characters = [CharacterVisualIdentity(name="Mansa Musa"), CharacterVisualIdentity(name="Ibn Battuta")]

    updated, images, cost = await service.execute(characters=characters)

    filenames = [character.reference_image_filename for character in updated]
    assert filenames == ["character_01_mansa_musa.png", "character_02_ibn_battuta.png"]
    assert len(images) == 2
    assert cost == pytest.approx(0.084)


# --- F9: reference portrait validation -------------------------------------------------


@pytest.mark.asyncio
async def test_execute_rejects_invalid_portrait_even_after_a_retry():
    from backend.services.image_validation_service import ImageValidationResult

    provider = FakeImageProvider(media_assets=[_media_asset(_data_uri(b"bad-1")), _media_asset(_data_uri(b"bad-2"))])
    validator = FakeValidationService(
        [
            ImageValidationResult(valid=False, issues=["multi-panel"], estimated_cost_usd=0.0),
            ImageValidationResult(valid=False, issues=["still multi-panel"], estimated_cost_usd=0.0),
        ]
    )
    service = CharacterReferenceImageService(
        image_generation_provider=provider, settings=Settings(image_validation_max_retries=1), image_validation_service=validator
    )
    characters = [CharacterVisualIdentity(name="Mansa Musa")]

    updated, images, cost = await service.execute(characters=characters)

    # F9: never accept an invalid reference portrait as the identity anchor —
    # even though two images were generated (one retry), neither is accepted.
    assert updated[0].reference_image_filename == ""
    assert images == {}
    assert len(provider.calls) == 2


@pytest.mark.asyncio
async def test_execute_accepts_portrait_that_becomes_valid_after_one_retry():
    from backend.services.image_validation_service import ImageValidationResult

    provider = FakeImageProvider(media_assets=[_media_asset(_data_uri(b"bad")), _media_asset(_data_uri(b"good"))])
    validator = FakeValidationService(
        [
            ImageValidationResult(valid=False, issues=["multi-panel"], estimated_cost_usd=0.0),
            ImageValidationResult(valid=True, estimated_cost_usd=0.0),
        ]
    )
    service = CharacterReferenceImageService(
        image_generation_provider=provider, settings=Settings(image_validation_max_retries=1), image_validation_service=validator
    )
    characters = [CharacterVisualIdentity(name="Mansa Musa")]

    updated, images, cost = await service.execute(characters=characters)

    assert updated[0].reference_image_filename == "character_01_mansa_musa.png"
    assert images[updated[0].reference_image_filename] == b"good"


@pytest.mark.asyncio
async def test_execute_accepts_portrait_immediately_when_validation_passes_first_try():
    from backend.services.image_validation_service import ImageValidationResult

    provider = FakeImageProvider(media_assets=[_media_asset(_data_uri(b"good"))])
    validator = FakeValidationService([ImageValidationResult(valid=True, estimated_cost_usd=0.0)])
    service = CharacterReferenceImageService(
        image_generation_provider=provider, settings=Settings(), image_validation_service=validator
    )
    characters = [CharacterVisualIdentity(name="Mansa Musa")]

    updated, images, cost = await service.execute(characters=characters)

    assert updated[0].reference_image_filename == "character_01_mansa_musa.png"
    assert len(provider.calls) == 1


@pytest.mark.asyncio
async def test_execute_one_rejected_character_does_not_block_the_next():
    from backend.services.image_validation_service import ImageValidationResult

    provider = FakeImageProvider(
        media_assets=[_media_asset(_data_uri(b"bad-1")), _media_asset(_data_uri(b"bad-1-retry")), _media_asset(_data_uri(b"good-2"))]
    )
    validator = FakeValidationService(
        [
            ImageValidationResult(valid=False, issues=["broken"], estimated_cost_usd=0.0),
            ImageValidationResult(valid=False, issues=["still broken"], estimated_cost_usd=0.0),
            ImageValidationResult(valid=True, estimated_cost_usd=0.0),
        ]
    )
    service = CharacterReferenceImageService(
        image_generation_provider=provider, settings=Settings(image_validation_max_retries=1), image_validation_service=validator
    )
    characters = [CharacterVisualIdentity(name="Mansa Musa"), CharacterVisualIdentity(name="Ibn Battuta")]

    updated, images, cost = await service.execute(characters=characters)

    assert updated[0].reference_image_filename == ""  # rejected
    assert updated[1].reference_image_filename == "character_02_ibn_battuta.png"  # accepted
    assert len(images) == 1


# --- F3: budget enforcement --------------------------------------------------------------


@pytest.mark.asyncio
async def test_execute_skips_portrait_when_budget_already_exhausted():
    provider = FakeImageProvider(media_assets=[_media_asset(_data_uri(b"x"))])
    service = CharacterReferenceImageService(image_generation_provider=provider, settings=Settings(maximum_video_budget_usd=5.0))
    characters = [CharacterVisualIdentity(name="Mansa Musa")]

    updated, images, cost = await service.execute(characters=characters, estimated_cost_so_far_usd=5.0)

    assert updated[0].reference_image_filename == ""
    assert images == {}
    assert cost == 0.0
    assert provider.calls == []


@pytest.mark.asyncio
async def test_execute_stops_affording_further_characters_once_budget_runs_out():
    provider = FakeImageProvider(media_assets=[_media_asset(_data_uri(b"a")), _media_asset(_data_uri(b"b"))])
    # Budget affords exactly one $0.042 portrait, not two.
    service = CharacterReferenceImageService(image_generation_provider=provider, settings=Settings(maximum_video_budget_usd=0.05))
    characters = [CharacterVisualIdentity(name="Mansa Musa"), CharacterVisualIdentity(name="Ibn Battuta")]

    updated, images, cost = await service.execute(characters=characters, estimated_cost_so_far_usd=0.0)

    assert updated[0].reference_image_filename != ""
    assert updated[1].reference_image_filename == ""
    assert len(images) == 1
    assert len(provider.calls) == 1
