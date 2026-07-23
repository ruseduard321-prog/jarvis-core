from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from backend.api.dependencies.auth import get_auth_service
from backend.api.dependencies.security import get_current_user
from backend.auth.auth_models import AuthSession, AuthUser
from backend.auth.auth_service import AuthService
from backend.core.config import settings

router = APIRouter(prefix="/auth")


class SignInRequest(BaseModel):
    """Request schema for sign-in."""

    email: str
    password: str


class RefreshRequest(BaseModel):
    """Request schema for token refresh."""

    refresh_token: str


@router.post("/sign-in", response_model=AuthSession)
async def sign_in(
    data: SignInRequest,
    service: AuthService = Depends(get_auth_service),
) -> AuthSession:
    """Authenticate a user and return a session."""
    # Fast path for development credentials, debug mode only—no service dependency needed
    if settings.debug and data.email == "dev@jarvis.local" and data.password == "dev-password":
        from backend.auth.dev_auth import create_dev_session
        return create_dev_session()
    return service.sign_in(email=data.email, password=data.password)


@router.post("/refresh", response_model=AuthSession)
async def refresh(
    data: RefreshRequest,
    service: AuthService = Depends(get_auth_service),
) -> AuthSession:
    """Refresh an access token using a refresh token."""
    return service.refresh_session(refresh_token=data.refresh_token)


@router.post("/sign-out")
async def sign_out() -> dict:
    """Sign out (clears the session client-side; no-op on the server)."""
    return {"ok": True}


@router.get("/me", response_model=AuthUser)
async def me(current_user: AuthUser = Depends(get_current_user)) -> AuthUser:
    """Return the authenticated user attached to the request state."""
    return current_user


@router.post("/dev-sign-in", response_model=AuthSession)
async def dev_sign_in() -> AuthSession:
    """Return a development session without Supabase (DEBUG=True only).

    Development credentials:
      email:    dev@jarvis.local
      password: dev-password

    The returned ``access_token`` is accepted by all API endpoints when
    ``DEBUG=True``.  This endpoint returns 404 in production.
    """
    if not settings.debug:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    from backend.auth.dev_auth import create_dev_session
    return create_dev_session()
