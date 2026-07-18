from datetime import datetime

from backend.core.database import DatabaseProvider
from backend.models.user import User
from backend.repositories.base_repository import BaseRepository
from backend.schemas.user import UserCreate


class UserRepository(BaseRepository[User]):
    """Repository for user domain operations."""

    def __init__(self, database: DatabaseProvider) -> None:
        super().__init__(database)

    async def list_users(self) -> list[User]:
        """Return a list of users."""
        return []

    async def create_user(self, data: UserCreate) -> User:
        """Create a new user."""
        return User(
            id="placeholder",
            email=data.email,
            full_name=data.full_name,
            created_at=datetime.utcnow(),
        )
