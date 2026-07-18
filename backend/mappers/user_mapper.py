from backend.mappers.base_mapper import BaseMapper
from backend.models.user import User
from backend.schemas.user_response import UserResponse


class UserMapper(BaseMapper[User, UserResponse]):
    """Map between database rows, domain models, and response models."""

    @staticmethod
    def from_row(row: dict) -> User:
        """Convert a database row into a User domain model."""
        return User(**row)

    @staticmethod
    def to_response(user: User) -> UserResponse:
        """Convert a User domain model into a response schema."""
        return UserResponse(**user.dict())
