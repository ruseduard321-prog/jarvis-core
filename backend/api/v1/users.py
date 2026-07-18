from fastapi import APIRouter, Depends

from backend.api.dependencies.users import get_user_service
from backend.schemas.user import UserCreate
from backend.schemas.user_response import UserResponse
from backend.services.user_service import UserService

router = APIRouter(prefix="/users")


@router.get("", response_model=list[UserResponse])
async def list_users(
    service: UserService = Depends(get_user_service),
) -> list[UserResponse]:
    """Return a list of users."""
    return await service.list_users()


@router.post("", response_model=UserResponse)
async def create_user(
    data: UserCreate,
    service: UserService = Depends(get_user_service),
) -> UserResponse:
    """Create a new user."""
    return await service.create_user(data)
