from fastapi import APIRouter, Depends
from pydantic import BaseModel

from backend.api.dependencies.auth import get_auth_service
from backend.api.dependencies.security import get_current_user
from backend.auth.auth_models import AuthSession, AuthUser
from backend.auth.auth_service import AuthService

router = APIRouter(prefix="/auth")


class SignInRequest(BaseModel):
    """Request schema for sign-in."""

    email: str
    password: str


@router.post("/sign-in", response_model=AuthSession)
async def sign_in(
    data: SignInRequest,
    service: AuthService = Depends(get_auth_service),
) -> AuthSession:
    """Authenticate a user and return a session."""
    return service.sign_in(email=data.email, password=data.password)


@router.get("/me", response_model=AuthUser)
async def me(current_user: AuthUser = Depends(get_current_user)) -> AuthUser:
    """Return the authenticated user attached to the request state."""
    return current_user
