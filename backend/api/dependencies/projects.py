from fastapi import Depends

from backend.core.dependencies import get_database
from backend.repositories.project_repository import ProjectRepository
from backend.services.project_service import ProjectService


def get_project_repository(database = Depends(get_database)) -> ProjectRepository:
    """Return a project repository instance."""
    return ProjectRepository(database)


def get_project_service(repository: ProjectRepository = Depends(get_project_repository)) -> ProjectService:
    """Return a project service instance."""
    return ProjectService(repository)
