from datetime import datetime

from pydantic import BaseModel


class ProjectResponse(BaseModel):
    """Output schema for project responses."""

    id: str
    name: str
    created_at: datetime
