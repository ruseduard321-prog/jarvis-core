from datetime import datetime

from pydantic import BaseModel, Field


class Agent(BaseModel):
    """Persistent agent business entity."""

    id: str
    slug: str
    owner_user_id: str
    name: str
    mission: str
    allowed_delegations: list[str] = Field(default_factory=list)
    is_active: bool
    created_at: datetime
    updated_at: datetime
