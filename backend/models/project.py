from datetime import datetime

from pydantic import BaseModel


class Project(BaseModel):
    """Project domain model."""

    id: str
    name: str
    created_at: datetime
