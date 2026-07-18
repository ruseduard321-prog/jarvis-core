from datetime import datetime

from pydantic import BaseModel


class UserResponse(BaseModel):
    """Output schema for user responses."""

    id: str
    email: str
    full_name: str | None
    created_at: datetime
