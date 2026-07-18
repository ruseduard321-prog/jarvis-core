from __future__ import annotations

from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from backend.auth.auth_models import AuthUser
from backend.auth.supabase_auth import SupabaseAuthClient
from backend.core.domain_exceptions import AuthenticationError


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """Middleware that authenticates requests using Supabase access tokens."""

    def __init__(self, app, auth_client: SupabaseAuthClient, **kwargs) -> None:
        super().__init__(app, **kwargs)
        self.auth_client = auth_client

    async def dispatch(self, request: Request, call_next: Callable[[Request], Response]) -> Response:
        """Authenticate the request and attach the user to request.state."""
        authorization = request.headers.get("authorization")
        if authorization is None:
            return await call_next(request)

        parts = authorization.split()
        if len(parts) != 2 or parts[0].lower() != "bearer" or not parts[1].strip():
            raise AuthenticationError("Invalid authorization header format")

        access_token = parts[1].strip()
        request.state.user = self.auth_client.validate_token(access_token)
        return await call_next(request)
