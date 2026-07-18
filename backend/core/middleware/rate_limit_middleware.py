from __future__ import annotations

import logging
from typing import Callable

from fastapi import status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from backend.core.rate_limit import (
    RateLimitStore,
    get_client_identifier,
    make_rate_limit_key,
)

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware that enforces rate limits per endpoint and client."""

    def __init__(self, app, store: RateLimitStore, default_limit: tuple[int, int], endpoint_limits: dict[str, tuple[int, int]] | None = None, **kwargs) -> None:
        super().__init__(app, **kwargs)
        self.store = store
        self.default_limit = default_limit
        self.endpoint_limits = endpoint_limits or {}

    async def dispatch(self, request: Request, call_next: Callable[[Request], Response]) -> Response:
        path = request.url.path
        identifier = get_client_identifier(request)
        namespace = "rate_limit"
        limit, window = self.endpoint_limits.get(path, self.default_limit)
        key = make_rate_limit_key(namespace, identifier, path)

        count, reset_timestamp = await self.store.increment(key, window)
        remaining = max(limit - count, 0)

        if count > limit:
            retry_after = reset_timestamp - int(__import__("time").time())
            logger.warning(
                "rate_limit_exceeded",
                extra={
                    "request_id": getattr(request.state, "request_id", "-"),
                    "path": path,
                    "client": identifier,
                    "limit": limit,
                    "window": window,
                    "count": count,
                },
            )
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error_code": "rate_limit_exceeded",
                    "message": "Too many requests",
                    "status_code": status.HTTP_429_TOO_MANY_REQUESTS,
                    "request_id": getattr(request.state, "request_id", "-"),
                },
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": str(remaining),
                    "X-RateLimit-Reset": str(reset_timestamp),
                },
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(reset_timestamp)
        return response
