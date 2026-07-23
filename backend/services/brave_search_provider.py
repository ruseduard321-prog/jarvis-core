from __future__ import annotations

import logging

import httpx

from backend.services.search_provider import SearchProvider

logger = logging.getLogger(__name__)

_BRAVE_SEARCH_ENDPOINT = "https://api.search.brave.com/res/v1/web/search"


class BraveSearchProvider(SearchProvider):
    """SearchProvider backed by the Brave Search API.

    A missing API key is a configuration error and raises immediately — silently
    returning no results would make a misconfigured key indistinguishable from a
    query that genuinely has no results, the exact ambiguity that made the prior
    DuckDuckGo-based failures hard to diagnose. Network, timeout, and non-2xx
    errors are treated as "no results" instead: ResearchWorkflowService already
    treats an empty result list as a clean failure path, and a transient
    search-provider hiccup shouldn't crash the workflow.
    """

    def __init__(self, api_key: str | None, timeout_seconds: float = 15.0) -> None:
        self._api_key = api_key
        self._timeout_seconds = timeout_seconds

    async def search(self, query: str, limit: int = 8) -> list[dict[str, str]]:
        if not query.strip():
            return []
        if not self._api_key:
            raise ValueError("BRAVE_SEARCH_API_KEY is not configured — cannot perform a Brave search.")

        headers = {
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "X-Subscription-Token": self._api_key,
        }
        params = {"q": query, "count": max(1, min(limit, 20))}

        try:
            async with httpx.AsyncClient(timeout=self._timeout_seconds) as client:
                response = await client.get(_BRAVE_SEARCH_ENDPOINT, headers=headers, params=params)
            response.raise_for_status()
            payload = response.json()
        except httpx.TimeoutException:
            logger.warning(
                "Brave search timed out", extra={"query": query, "timeout_seconds": self._timeout_seconds}
            )
            return []
        except httpx.HTTPStatusError as exc:
            logger.warning(
                "Brave search returned an error status",
                extra={"query": query, "status_code": exc.response.status_code},
            )
            return []
        except httpx.HTTPError as exc:
            logger.warning("Brave search request failed", extra={"query": query, "error": str(exc)})
            return []
        except ValueError:
            logger.warning("Brave search returned a non-JSON response", extra={"query": query})
            return []

        web_results = ((payload or {}).get("web") or {}).get("results") or []
        results: list[dict[str, str]] = []
        for item in web_results:
            if not isinstance(item, dict):
                continue
            url = str(item.get("url", "")).strip()
            if not url:
                continue
            results.append(
                {
                    "title": str(item.get("title", "")).strip() or url,
                    "url": url,
                    "snippet": str(item.get("description", "")).strip(),
                    "source": "brave",
                }
            )
            if len(results) >= limit:
                break

        return results
