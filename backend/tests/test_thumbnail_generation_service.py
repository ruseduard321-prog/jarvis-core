from __future__ import annotations

import pytest

from backend.core.config import Settings
from backend.core.media_asset import MediaAsset
from backend.core.provider_exceptions import TransientProviderError
from backend.services.thumbnail_generation_service import ThumbnailGenerationService


class FakeImageProvider:
    def __init__(self, *, media_asset: MediaAsset | None = None, raises: Exception | None = None):
        self._media_asset = media_asset
        self._raises = raises

    async def generate_image(self, *, prompt, size=None, quality=None, model=None, reference_image=None):
        if self._raises:
            raise self._raises
        return self._media_asset


def _media_asset(source: str) -> MediaAsset:
    return MediaAsset(
        id="asset-1",
        type="image",
        source=source,
        provider="openai-image-generation",
        mime_type="image/png",
        width=1024,
        height=1024,
        prompt="a scene",
        metadata={"model": "gpt-image-1"},
    )


@pytest.mark.asyncio
async def test_execute_skips_when_prompt_is_empty():
    service = ThumbnailGenerationService(image_generation_provider=FakeImageProvider(), settings=Settings())

    asset, image_bytes = await service.execute("   ")

    assert asset.status == "SKIPPED"
    assert image_bytes is None


@pytest.mark.asyncio
async def test_execute_decodes_base64_data_uri_into_bytes():
    import base64

    raw = b"raw-png-bytes"
    data_uri = f"data:image/png;base64,{base64.b64encode(raw).decode('ascii')}"
    provider = FakeImageProvider(media_asset=_media_asset(data_uri))
    service = ThumbnailGenerationService(image_generation_provider=provider, settings=Settings())

    asset, image_bytes = await service.execute("a thumbnail prompt")

    assert asset.status == "SUCCESS"
    assert asset.resolution == "1024x1024"
    assert image_bytes == raw


@pytest.mark.asyncio
async def test_execute_fails_when_source_is_not_decodable():
    provider = FakeImageProvider(media_asset=_media_asset("generated"))
    service = ThumbnailGenerationService(image_generation_provider=provider, settings=Settings())

    asset, image_bytes = await service.execute("a thumbnail prompt")

    assert asset.status == "FAILED"
    assert image_bytes is None


@pytest.mark.asyncio
async def test_execute_never_raises_on_provider_failure():
    provider = FakeImageProvider(raises=TransientProviderError("rate limited"))
    service = ThumbnailGenerationService(image_generation_provider=provider, settings=Settings())

    asset, image_bytes = await service.execute("a thumbnail prompt")

    assert asset.status == "FAILED"
    assert image_bytes is None


@pytest.mark.asyncio
async def test_execute_skips_when_budget_already_exhausted():
    provider = FakeImageProvider(media_asset=_media_asset("generated"))
    service = ThumbnailGenerationService(image_generation_provider=provider, settings=Settings())

    asset, image_bytes = await service.execute("a thumbnail prompt", estimated_cost_so_far_usd=5.0)

    assert asset.status == "SKIPPED"
    assert "budget exhausted" in asset.error
    assert image_bytes is None
