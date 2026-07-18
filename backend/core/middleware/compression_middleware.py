from __future__ import annotations

from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp, Receive, Scope, Send
from starlette.middleware.gzip import GZipMiddleware as StarletteGZipMiddleware

from backend.core.config import settings


class CompressionMiddleware(StarletteGZipMiddleware):
    """GZip compression middleware with configurable minimum response size."""

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app, minimum_size=settings.gzip_minimum_size)
