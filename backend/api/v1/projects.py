from fastapi import APIRouter, Depends

from backend.api.dependencies.projects import get_project_service
from backend.schemas.project import ProjectCreate
from backend.schemas.project_response import ProjectResponse
from backend.services.project_service import ProjectService

router = APIRouter(prefix="/projects")


@router.get("", response_model=list[ProjectResponse])
async def list_projects(
    service: ProjectService = Depends(get_project_service),
) -> list[ProjectResponse]:
    """Return a list of projects."""
    return await service.list_projects()


@router.post("", response_model=ProjectResponse)
async def create_project(
    data: ProjectCreate,
    service: ProjectService = Depends(get_project_service),
) -> ProjectResponse:
    """Create a new project."""
    return await service.create_project(data)
