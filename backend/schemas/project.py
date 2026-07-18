from pydantic import BaseModel, constr


class ProjectCreate(BaseModel):
    """Input schema for creating a project."""

    name: constr(strip_whitespace=True, min_length=3, max_length=100)
