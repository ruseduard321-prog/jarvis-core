from __future__ import annotations

import base64
from types import SimpleNamespace

import pytest

from backend.core.config import Settings
from backend.core.provider_exceptions import PermanentProviderError
from backend.services.openai_image_generation_provider import OpenAIImageGenerationProvider


class FakeOpenAIProvider:
    def __init__(self, client) -> None:
        self._client = client

    async def get_client(self):
        return self._client


def _make_client(b64_json: str | None):
    async def _generate(**kwargs):
        return SimpleNamespace(data=[SimpleNamespace(b64_json=b64_json)])

    return SimpleNamespace(images=SimpleNamespace(generate=_generate))


def _make_edit_capable_client(*, edit_b64_json: str | None = None, generate_b64_json: str | None = None, edit_raises: Exception | None = None):
    calls = {"generate": [], "edit": []}

    async def _generate(**kwargs):
        calls["generate"].append(kwargs)
        return SimpleNamespace(data=[SimpleNamespace(b64_json=generate_b64_json)])

    async def _edit(**kwargs):
        calls["edit"].append(kwargs)
        if edit_raises:
            raise edit_raises
        return SimpleNamespace(data=[SimpleNamespace(b64_json=edit_b64_json)])

    client = SimpleNamespace(images=SimpleNamespace(generate=_generate, edit=_edit))
    return client, calls


@pytest.mark.asyncio
async def test_generate_image_decodes_and_embeds_base64_data_uri():
    raw_bytes = b"fake-png-bytes"
    b64_json = base64.b64encode(raw_bytes).decode("ascii")
    client = _make_client(b64_json)
    provider = OpenAIImageGenerationProvider(openai_llm_provider=FakeOpenAIProvider(client), settings=Settings())

    asset = await provider.generate_image(prompt="a cat", size="512x512")

    assert asset.source == f"data:image/png;base64,{b64_json}"
    assert asset.width == 512
    assert asset.height == 512
    decoded = OpenAIImageGenerationProvider.decode_image_bytes(asset.source)
    assert decoded == raw_bytes


@pytest.mark.asyncio
async def test_generate_image_raises_permanent_error_when_no_data():
    client = _make_client(None)
    provider = OpenAIImageGenerationProvider(openai_llm_provider=FakeOpenAIProvider(client), settings=Settings())

    with pytest.raises(PermanentProviderError):
        await provider.generate_image(prompt="a cat")


def test_decode_image_bytes_returns_none_for_non_data_uri():
    assert OpenAIImageGenerationProvider.decode_image_bytes("generated") is None


@pytest.mark.asyncio
async def test_generate_image_uses_edit_endpoint_when_reference_image_given():
    raw_bytes = b"edited-png-bytes"
    b64_json = base64.b64encode(raw_bytes).decode("ascii")
    client, calls = _make_edit_capable_client(edit_b64_json=b64_json)
    provider = OpenAIImageGenerationProvider(openai_llm_provider=FakeOpenAIProvider(client), settings=Settings())

    asset = await provider.generate_image(prompt="a king", size="1024x1024", reference_image=b"reference-bytes")

    assert asset.source == f"data:image/png;base64,{b64_json}"
    assert asset.metadata["used_reference_image"] is True
    assert len(calls["edit"]) == 1
    assert len(calls["generate"]) == 0


@pytest.mark.asyncio
async def test_generate_image_falls_back_to_generate_when_edit_fails():
    raw_bytes = b"fallback-png-bytes"
    b64_json = base64.b64encode(raw_bytes).decode("ascii")
    client, calls = _make_edit_capable_client(generate_b64_json=b64_json, edit_raises=RuntimeError("edit unsupported"))
    provider = OpenAIImageGenerationProvider(openai_llm_provider=FakeOpenAIProvider(client), settings=Settings())

    asset = await provider.generate_image(prompt="a king", size="1024x1024", reference_image=b"reference-bytes")

    assert asset.source == f"data:image/png;base64,{b64_json}"
    assert asset.metadata["used_reference_image"] is False
    assert len(calls["edit"]) == 1
    assert len(calls["generate"]) == 1


@pytest.mark.asyncio
async def test_generate_image_ignores_reference_image_param_when_none():
    raw_bytes = b"plain-png-bytes"
    b64_json = base64.b64encode(raw_bytes).decode("ascii")
    client, calls = _make_edit_capable_client(generate_b64_json=b64_json)
    provider = OpenAIImageGenerationProvider(openai_llm_provider=FakeOpenAIProvider(client), settings=Settings())

    asset = await provider.generate_image(prompt="a king", size="1024x1024")

    assert asset.metadata["used_reference_image"] is False
    assert len(calls["edit"]) == 0
    assert len(calls["generate"]) == 1
