from datetime import datetime

from pydantic import BaseModel


class User(BaseModel):
    """User domain model."""

    id: str
    email: str
    full_name: str | None
    created_at: datetime
