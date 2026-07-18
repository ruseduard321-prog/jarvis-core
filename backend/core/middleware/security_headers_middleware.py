from __future__ import annotations

from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from backend.core.config import settings


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware that applies standard HTTP security headers."""

    async def dispatch(self, request: Request, call_next: Callable[[Request], Response]) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers[
            "Permissions-Policy"
        ] = "geolocation=(), camera=(), microphone=(), payment=()"
        if not settings.debug:
            response.headers["Strict-Transport-Security"] = settings.hsts_header
        return response
