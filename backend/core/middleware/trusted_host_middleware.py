from __future__ import annotations

from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from backend.core.config import settings


class TrustedHostMiddleware(BaseHTTPMiddleware):
    """Middleware that validates the Host header against configured trusted hosts."""

    async def dispatch(self, request: Request, call_next: Callable[[Request], Response]) -> Response:
        host = request.headers.get("host", "")
        trusted_hosts = settings.trusted_hosts
        if trusted_hosts != ["*"] and host not in trusted_hosts:
            return Response(status_code=400, content=b"Invalid Host header")
        return await call_next(request)
