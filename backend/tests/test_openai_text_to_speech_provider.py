from __future__ import annotations

from types import SimpleNamespace

import pytest

from backend.core.config import Settings
from backend.services.openai_text_to_speech_provider import OpenAITextToSpeechProvider


class FakeOpenAIProvider:
    def __init__(self, client) -> None:
        self._client = client

    async def get_client(self):
        return self._client


def _make_client(audio_bytes: bytes):
    async def _create(**kwargs):
        return SimpleNamespace(content=audio_bytes)

    return SimpleNamespace(audio=SimpleNamespace(speech=SimpleNamespace(create=_create)))


@pytest.mark.asyncio
async def test_generate_speech_returns_asset_and_bytes():
    client = _make_client(b"fake-mp3-bytes")
    provider = OpenAITextToSpeechProvider(openai_llm_provider=FakeOpenAIProvider(client), settings=Settings())

    asset, audio_bytes = await provider.generate_speech(text="hello world this is a test", speed=1.0)

    assert audio_bytes == b"fake-mp3-bytes"
    assert asset.status == "SUCCESS"
    assert asset.provider == "openai-tts"
    assert asset.duration > 0


@pytest.mark.asyncio
async def test_generate_speech_reads_via_aread_when_content_missing():
    async def _create(**kwargs):
        class _Response:
            content = None

            async def aread(self):
                return b"streamed-bytes"

        return _Response()

    client = SimpleNamespace(audio=SimpleNamespace(speech=SimpleNamespace(create=_create)))
    provider = OpenAITextToSpeechProvider(openai_llm_provider=FakeOpenAIProvider(client), settings=Settings())

    _, audio_bytes = await provider.generate_speech(text="hello")

    assert audio_bytes == b"streamed-bytes"


@pytest.mark.asyncio
async def test_generate_speech_splits_long_text_into_multiple_calls():
    calls: list[str] = []

    async def _create(**kwargs):
        calls.append(kwargs["input"])
        return SimpleNamespace(content=b"chunk-bytes")

    client = SimpleNamespace(audio=SimpleNamespace(speech=SimpleNamespace(create=_create)))
    provider = OpenAITextToSpeechProvider(openai_llm_provider=FakeOpenAIProvider(client), settings=Settings())

    long_text = ("This is a sentence. " * 500).strip()
    _, audio_bytes = await provider.generate_speech(text=long_text)

    assert len(calls) > 1
    assert all(len(chunk) <= 4000 for chunk in calls)
    assert audio_bytes == b"chunk-bytes" * len(calls)


@pytest.mark.asyncio
async def test_generate_speech_passes_instructions_when_provided():
    calls: list[dict] = []

    async def _create(**kwargs):
        calls.append(kwargs)
        return SimpleNamespace(content=b"fake-mp3-bytes")

    client = SimpleNamespace(audio=SimpleNamespace(speech=SimpleNamespace(create=_create)))
    provider = OpenAITextToSpeechProvider(openai_llm_provider=FakeOpenAIProvider(client), settings=Settings())

    await provider.generate_speech(text="hello", instructions="Speak like a documentary narrator.")

    assert calls[0]["instructions"] == "Speak like a documentary narrator."


@pytest.mark.asyncio
async def test_generate_speech_omits_instructions_when_not_provided():
    calls: list[dict] = []

    async def _create(**kwargs):
        calls.append(kwargs)
        return SimpleNamespace(content=b"fake-mp3-bytes")

    client = SimpleNamespace(audio=SimpleNamespace(speech=SimpleNamespace(create=_create)))
    provider = OpenAITextToSpeechProvider(openai_llm_provider=FakeOpenAIProvider(client), settings=Settings())

    await provider.generate_speech(text="hello")

    assert "instructions" not in calls[0]


def test_estimate_duration_scales_with_word_count_and_speed():
    provider = OpenAITextToSpeechProvider(openai_llm_provider=None, settings=Settings())
    short = provider._estimate_duration("one two three", speed=1.0)
    long = provider._estimate_duration(" ".join(["word"] * 300), speed=1.0)
    assert long > short

    normal = provider._estimate_duration("word " * 150, speed=1.0)
    fast = provider._estimate_duration("word " * 150, speed=2.0)
    assert fast < normal
