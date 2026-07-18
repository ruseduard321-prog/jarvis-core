from backend.mappers.base_mapper import BaseMapper
from backend.models.project import Project
from backend.schemas.project_response import ProjectResponse


class ProjectMapper(BaseMapper[Project, ProjectResponse]):
    """Map between database rows, domain models, and response models."""

    @staticmethod
    def from_row(row: dict) -> Project:
        """Convert a database row into a Project domain model."""
        return Project(**row)

    @staticmethod
    def to_response(project: Project) -> ProjectResponse:
        """Convert a Project domain model into a response schema."""
        return ProjectResponse(**project.dict())
