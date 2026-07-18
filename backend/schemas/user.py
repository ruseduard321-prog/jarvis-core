from pydantic import BaseModel


class UserCreate(BaseModel):
    """Input schema for creating a user."""

    email: str
    full_name: str | None = None
