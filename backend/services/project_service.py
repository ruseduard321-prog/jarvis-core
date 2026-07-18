from backend.models.project import Project
from backend.repositories.base import BaseRepository
from backend.schemas.project import ProjectCreate
from backend.services.base import BaseService


class ProjectService(BaseService):
    """Service layer for project domain operations."""

    def __init__(self, repository: BaseRepository) -> None:
        super().__init__(repository)

    async def list_projects(self) -> list[Project]:
        """Return a list of projects."""
        return await self.repository.list_projects()

    async def create_project(self, data: ProjectCreate) -> Project:
        """Create a new project."""
        return await self.repository.create_project(data)
