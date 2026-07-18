import logging

from backend.core.database import DatabaseProvider
from backend.core.domain_exceptions import DatabaseUnavailableError, RepositoryError
from backend.mappers.project_mapper import ProjectMapper
from backend.models.project import Project
from backend.repositories.base_repository import BaseRepository
from backend.schemas.project import ProjectCreate

logger = logging.getLogger(__name__)


class ProjectRepository(BaseRepository[Project]):
    """Repository for project domain operations."""

    async def list_projects(self) -> list[Project]:
        """Return a list of projects from Supabase."""
        if not await self.database.health_check():
            return []

        try:
            assert hasattr(self.database, 'client')
            client = getattr(self.database, 'client')
            if client is None:
                return []

            response = client.table('projects').select('*').execute()
            rows = getattr(response, 'data', None) or []

            return [ProjectMapper.from_row(row) for row in rows]
        except Exception as exc:
            logger.exception("Error listing projects from Supabase")
            raise RepositoryError() from exc

    async def create_project(self, data: ProjectCreate) -> Project:
        """Create a new project in Supabase."""
        if not await self.database.health_check():
            raise DatabaseUnavailableError()

        try:
            assert hasattr(self.database, 'client')
            client = getattr(self.database, 'client')
            if client is None:
                raise DatabaseUnavailableError()

            response = client.table('projects').insert(data.dict()).select('*').execute()
            rows = getattr(response, 'data', None) or []
            if not rows:
                raise DatabaseUnavailableError()

            return ProjectMapper.from_row(rows[0])
        except Exception as exc:
            logger.exception("Error creating project in Supabase")
            raise RepositoryError() from exc
