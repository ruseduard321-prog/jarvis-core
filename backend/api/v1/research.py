from __future__ import annotations

from fastapi import APIRouter, Depends

from backend.api.dependencies.security import get_current_user
from backend.auth.auth_models import AuthUser
from backend.core.dependencies import (
    get_content_finalization_workflow_service,
    get_research_workflow_service,
    get_writer_workflow_service,
)
from backend.schemas.research import (
    PublishingPackage,
    PublishingPackageRequest,
    ResearchPackage,
    ResearchPackageRequest,
    ScriptDraft,
    ScriptDraftRequest,
)
from backend.services.content_finalization_workflow_service import ContentFinalizationWorkflowService
from backend.services.research_workflow_service import ResearchWorkflowService
from backend.services.writer_workflow_service import WriterWorkflowService

router = APIRouter(prefix="/research", tags=["research"])


@router.post("/package", response_model=ResearchPackage)
async def generate_research_package(
    request: ResearchPackageRequest,
    current_user: AuthUser = Depends(get_current_user),
    workflow_service: ResearchWorkflowService = Depends(get_research_workflow_service),
) -> ResearchPackage:
    """Generate a structured research package using the production research workflow."""

    return await workflow_service.execute(
        topic=request.topic,
        constraints=request.constraints,
        user_id=current_user.id,
    )


@router.post("/script-draft", response_model=ScriptDraft)
async def generate_script_draft(
    request: ScriptDraftRequest,
    current_user: AuthUser = Depends(get_current_user),
    workflow_service: WriterWorkflowService = Depends(get_writer_workflow_service),
) -> ScriptDraft:
    """Generate a YouTube-ready script draft from an existing research package."""

    return await workflow_service.execute(
        research_package=request.research_package,
        duration_profile=request.duration_profile,
        user_id=current_user.id,
    )


@router.post("/publishing-package", response_model=PublishingPackage)
async def generate_publishing_package(
    request: PublishingPackageRequest,
    current_user: AuthUser = Depends(get_current_user),
    workflow_service: ContentFinalizationWorkflowService = Depends(get_content_finalization_workflow_service),
) -> PublishingPackage:
    """Generate a publication-ready package from an existing script draft."""

    return await workflow_service.execute(
        script_draft=request.script_draft,
        user_id=current_user.id,
    )
