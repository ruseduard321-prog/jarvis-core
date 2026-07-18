from fastapi import Depends

from backend.core.dependencies import get_database
from backend.repositories.user_repository import UserRepository
from backend.services.user_service import UserService


def get_user_repository(database = Depends(get_database)) -> UserRepository:
    """Return a user repository instance."""
    return UserRepository(database)


def get_user_service(repository: UserRepository = Depends(get_user_repository)) -> UserService:
    """Return a user service instance."""
    return UserService(repository)
