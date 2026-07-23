from __future__ import annotations

import pytest

from backend.core.config import Settings
from backend.core.provider_exceptions import PermanentProviderError
from backend.schemas.assets import VoiceAsset
from backend.schemas.research import ReviewedScript
from backend.services.voice_generation_service import VoiceGenerationService


def _reviewed_script(text: str = "Hello narration.") -> ReviewedScript:
    return ReviewedScript(
        topic="Test Topic",
        revised_script=text,
        quality_score=90.0,
        readability_score=90.0,
        engagement_score=90.0,
        status="success",
        metadata={"status": "success"},
    )


class FakeTTSProvider:
    def __init__(self, *, asset: VoiceAsset | None = None, audio: bytes | None = None, raises: Exception | None = None):
        self._asset = asset
        self._audio = audio
        self._raises = raises

    async def generate_speech(self, *, text, model=None, voice=None, speed=None, language=None, instructions=None):
        self.called_with = {
            "text": text,
            "model": model,
            "voice": voice,
            "speed": speed,
            "instructions": instructions,
        }
        if self._raises:
            raise self._raises
        return self._asset, self._audio


class FakeNarrationProcessingService:
    """Passthrough fake — the real ffmpeg loudnorm pass is exercised in
    test_narration_processing_service.py, not here."""

    def process(self, audio_bytes: bytes) -> bytes:
        return audio_bytes


@pytest.mark.asyncio
async def test_execute_skips_when_script_is_empty():
    service = VoiceGenerationService(
        text_to_speech_provider=FakeTTSProvider(),
        settings=Settings(),
        narration_processing_service=FakeNarrationProcessingService(),
    )

    asset, audio = await service.execute(_reviewed_script(""))

    assert asset.status == "SKIPPED"
    assert audio is None


@pytest.mark.asyncio
async def test_execute_returns_success_asset_and_bytes():
    expected_asset = VoiceAsset(provider="openai-tts", generation_time="2026-01-01T00:00:00Z", status="SUCCESS")
    provider = FakeTTSProvider(asset=expected_asset, audio=b"audio-bytes")
    service = VoiceGenerationService(
        text_to_speech_provider=provider,
        settings=Settings(),
        narration_processing_service=FakeNarrationProcessingService(),
    )

    asset, audio = await service.execute(_reviewed_script())

    assert asset.provider == expected_asset.provider
    assert asset.status == "SUCCESS"
    assert asset.voice_profile == "documentary_male"
    assert audio == b"audio-bytes"
    assert provider.called_with["model"] == "gpt-4o-mini-tts"
    assert provider.called_with["voice"] == "onyx"
    assert provider.called_with["instructions"]


@pytest.mark.asyncio
async def test_execute_never_raises_on_provider_failure():
    provider = FakeTTSProvider(raises=PermanentProviderError("boom"))
    service = VoiceGenerationService(
        text_to_speech_provider=provider,
        settings=Settings(),
        narration_processing_service=FakeNarrationProcessingService(),
    )

    asset, audio = await service.execute(_reviewed_script())

    assert asset.status == "FAILED"
    assert audio is None


@pytest.mark.asyncio
async def test_execute_never_raises_on_unexpected_exception():
    provider = FakeTTSProvider(raises=RuntimeError("unexpected"))
    service = VoiceGenerationService(
        text_to_speech_provider=provider,
        settings=Settings(),
        narration_processing_service=FakeNarrationProcessingService(),
    )

    asset, audio = await service.execute(_reviewed_script())

    assert asset.status == "FAILED"
    assert audio is None


@pytest.mark.asyncio
async def test_execute_treats_non_success_asset_as_no_bytes():
    skipped_asset = VoiceAsset(provider="none", generation_time="2026-01-01T00:00:00Z", status="SKIPPED")
    provider = FakeTTSProvider(asset=skipped_asset, audio=b"should-be-ignored")
    service = VoiceGenerationService(
        text_to_speech_provider=provider,
        settings=Settings(),
        narration_processing_service=FakeNarrationProcessingService(),
    )

    asset, audio = await service.execute(_reviewed_script())

    assert asset is skipped_asset
    assert audio is None
