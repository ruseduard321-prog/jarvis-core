from backend.models.user import User
from backend.repositories.base_repository import BaseRepository
from backend.schemas.user import UserCreate
from backend.services.base import BaseService


class UserService(BaseService):
    """Service layer for user domain operations."""

    def __init__(self, repository: BaseRepository[User]) -> None:
        super().__init__(repository)

    async def list_users(self) -> list[User]:
        """Return a list of users."""
        return await self.repository.list_users()

    async def create_user(self, data: UserCreate) -> User:
        """Create a new user."""
        return await self.repository.create_user(data)
