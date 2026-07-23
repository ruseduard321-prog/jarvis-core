from __future__ import annotations

from types import SimpleNamespace

import pytest

from backend.core.config import Settings
from backend.services.openai_speech_to_text_provider import OpenAISpeechToTextProvider


class FakeOpenAIProvider:
    def __init__(self, client) -> None:
        self._client = client

    async def get_client(self):
        return self._client


@pytest.mark.asyncio
async def test_transcribe_returns_asset_and_text():
    async def _create(**kwargs):
        return SimpleNamespace(text="hello world", language="en")

    client = SimpleNamespace(audio=SimpleNamespace(transcriptions=SimpleNamespace(create=_create)))
    provider = OpenAISpeechToTextProvider(openai_llm_provider=FakeOpenAIProvider(client), settings=Settings())

    asset, text = await provider.transcribe(audio_bytes=b"fake-audio")

    assert text == "hello world"
    assert asset.status == "SUCCESS"
    assert asset.language == "en"
    assert asset.provider == "openai-stt"


@pytest.mark.asyncio
async def test_transcribe_falls_back_to_requested_language_when_not_detected():
    async def _create(**kwargs):
        return SimpleNamespace(text="bonjour", language=None)

    client = SimpleNamespace(audio=SimpleNamespace(transcriptions=SimpleNamespace(create=_create)))
    provider = OpenAISpeechToTextProvider(openai_llm_provider=FakeOpenAIProvider(client), settings=Settings())

    asset, _ = await provider.transcribe(audio_bytes=b"fake-audio", language="fr")

    assert asset.language == "fr"
