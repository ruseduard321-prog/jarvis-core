from __future__ import annotations

import httpx
import pytest

from backend.services.brave_search_provider import BraveSearchProvider


def _patch_transport(monkeypatch: pytest.MonkeyPatch, handler) -> None:
    """Redirect BraveSearchProvider's httpx.AsyncClient to an in-memory MockTransport
    so tests never touch the network, while still exercising real httpx request/
    response handling (headers, params, status codes, JSON decoding)."""

    real_async_client = httpx.AsyncClient

    def _client_factory(*args, **kwargs):
        kwargs.pop("timeout", None)
        kwargs["transport"] = httpx.MockTransport(handler)
        return real_async_client(*args, **kwargs)

    monkeypatch.setattr("backend.services.brave_search_provider.httpx.AsyncClient", _client_factory)


@pytest.mark.asyncio
async def test_raises_when_api_key_missing():
    provider = BraveSearchProvider(api_key=None)

    with pytest.raises(ValueError):
        await provider.search(query="roanoke colony")


@pytest.mark.asyncio
async def test_returns_empty_list_for_blank_query():
    provider = BraveSearchProvider(api_key="test-key")

    assert await provider.search(query="   ") == []


@pytest.mark.asyncio
async def test_sends_subscription_token_and_parses_results(monkeypatch: pytest.MonkeyPatch):
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["headers"] = request.headers
        captured["url"] = request.url
        return httpx.Response(
            200,
            json={
                "web": {
                    "results": [
                        {"title": "Roanoke Colony", "url": "https://example.com/a", "description": "An overview."},
                        {"title": "Lost Colony", "url": "https://example.com/b", "description": "More detail."},
                    ]
                }
            },
        )

    _patch_transport(monkeypatch, handler)
    provider = BraveSearchProvider(api_key="secret-token")

    results = await provider.search(query="roanoke colony", limit=8)

    assert captured["headers"]["x-subscription-token"] == "secret-token"
    assert "roanoke" in str(captured["url"]).lower()
    assert results == [
        {"title": "Roanoke Colony", "url": "https://example.com/a", "snippet": "An overview.", "source": "brave"},
        {"title": "Lost Colony", "url": "https://example.com/b", "snippet": "More detail.", "source": "brave"},
    ]


@pytest.mark.asyncio
async def test_truncates_results_to_requested_limit(monkeypatch: pytest.MonkeyPatch):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "web": {
                    "results": [
                        {"title": f"Result {i}", "url": f"https://example.com/{i}", "description": ""}
                        for i in range(5)
                    ]
                }
            },
        )

    _patch_transport(monkeypatch, handler)
    provider = BraveSearchProvider(api_key="secret-token")

    results = await provider.search(query="roanoke colony", limit=2)

    assert len(results) == 2


@pytest.mark.asyncio
async def test_skips_results_missing_a_url(monkeypatch: pytest.MonkeyPatch):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"web": {"results": [{"title": "No URL", "description": "..."}]}},
        )

    _patch_transport(monkeypatch, handler)
    provider = BraveSearchProvider(api_key="secret-token")

    assert await provider.search(query="roanoke colony") == []


@pytest.mark.asyncio
async def test_returns_empty_list_when_web_key_missing(monkeypatch: pytest.MonkeyPatch):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={})

    _patch_transport(monkeypatch, handler)
    provider = BraveSearchProvider(api_key="secret-token")

    assert await provider.search(query="roanoke colony") == []


@pytest.mark.asyncio
async def test_returns_empty_list_on_timeout(monkeypatch: pytest.MonkeyPatch):
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.TimeoutException("timed out", request=request)

    _patch_transport(monkeypatch, handler)
    provider = BraveSearchProvider(api_key="secret-token", timeout_seconds=1.0)

    assert await provider.search(query="roanoke colony") == []


@pytest.mark.asyncio
async def test_returns_empty_list_on_http_error_status(monkeypatch: pytest.MonkeyPatch):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(429, json={"error": "rate limited"})

    _patch_transport(monkeypatch, handler)
    provider = BraveSearchProvider(api_key="secret-token")

    assert await provider.search(query="roanoke colony") == []


@pytest.mark.asyncio
async def test_returns_empty_list_on_malformed_json(monkeypatch: pytest.MonkeyPatch):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=b"not json")

    _patch_transport(monkeypatch, handler)
    provider = BraveSearchProvider(api_key="secret-token")

    assert await provider.search(query="roanoke colony") == []
