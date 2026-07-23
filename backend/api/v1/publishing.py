from __future__ import annotations

from fastapi import APIRouter, Depends

from backend.api.dependencies.security import get_current_user
from backend.auth.auth_models import AuthUser
from backend.core.dependencies import get_publishing_service
from backend.schemas.publishing import PublishedVideo
from backend.schemas.research import PublishingPackage
from backend.services.publishing_service import PublishingService

router = APIRouter(prefix="/publishing", tags=["publishing"])


@router.post("/youtube", response_model=PublishedVideo)
async def publish_to_youtube(
    request: PublishingPackage,
    current_user: AuthUser = Depends(get_current_user),
    publishing_service: PublishingService = Depends(get_publishing_service),
) -> PublishedVideo:
    """Publish a finalized publishing package to YouTube."""

    return await publishing_service.publish_to_youtube(
        publishing_package=request,
        user_id=current_user.id,
    )
