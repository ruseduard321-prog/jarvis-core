from __future__ import annotations

from pathlib import Path
from typing import Any

import httpx


class ToolResourceLoaderService:
    """Shared resource loader for URL and local file inputs used by reader tools."""

    # Many real sites (Wikipedia included) return 403 Forbidden for requests with no
    # User-Agent at all — a generic, honest identifier is enough to pass that check.
    _DEFAULT_HEADERS = {"User-Agent": "JarvisResearchBot/1.0 (+https://jarvis.local; research tooling)"}

    def __init__(self, timeout_seconds: float = 15.0) -> None:
        self._timeout_seconds = timeout_seconds

    async def load_text(
        self,
        *,
        path: str | None = None,
        url: str | None = None,
        encoding: str | None = None,
    ) -> tuple[str, dict[str, Any]]:
        if path:
            file_path = Path(path)
            raw = file_path.read_bytes()
            detected = encoding or self._guess_encoding(raw)
            return raw.decode(detected, errors="replace"), {
                "source": "file",
                "path": str(file_path),
                "encoding": detected,
            }

        if url:
            async with httpx.AsyncClient(
                timeout=self._timeout_seconds, follow_redirects=True, headers=self._DEFAULT_HEADERS
            ) as client:
                response = await client.get(url)
            response.raise_for_status()
            raw = response.content
            detected = encoding or response.encoding or self._guess_encoding(raw)
            return raw.decode(detected, errors="replace"), {
                "source": "url",
                "url": str(response.url),
                "status_code": response.status_code,
                "content_type": response.headers.get("content-type", ""),
                "encoding": detected,
            }

        raise ValueError("Provide either 'path' or 'url'.")

    async def load_bytes(
        self,
        *,
        path: str | None = None,
        url: str | None = None,
    ) -> tuple[bytes, dict[str, Any]]:
        if path:
            file_path = Path(path)
            return file_path.read_bytes(), {
                "source": "file",
                "path": str(file_path),
            }

        if url:
            async with httpx.AsyncClient(
                timeout=self._timeout_seconds, follow_redirects=True, headers=self._DEFAULT_HEADERS
            ) as client:
                response = await client.get(url)
            response.raise_for_status()
            return response.content, {
                "source": "url",
                "url": str(response.url),
                "status_code": response.status_code,
                "content_type": response.headers.get("content-type", ""),
            }

        raise ValueError("Provide either 'path' or 'url'.")

    def _guess_encoding(self, data: bytes) -> str:
        if data.startswith(b"\xef\xbb\xbf"):
            return "utf-8-sig"
        if data.startswith(b"\xff\xfe") or data.startswith(b"\xfe\xff"):
            return "utf-16"
        return "utf-8"
