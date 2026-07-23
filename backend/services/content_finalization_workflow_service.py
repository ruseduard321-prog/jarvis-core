from __future__ import annotations

from backend.schemas.research import PublishingPackage, ScriptDraft
from backend.services.media_workflow_service import MediaWorkflowService
from backend.services.publishing_package_workflow_service import PublishingPackageWorkflowService
from backend.services.review_workflow_service import ReviewWorkflowService


class ContentFinalizationWorkflowService:
    """Thin composition facade preserving the original review+media+publishing signature
    for `backend/api/v1/research.py`'s `/research/publishing-package` endpoint. The actual
    logic lives exactly once in `ReviewWorkflowService` -> `MediaWorkflowService` ->
    `PublishingPackageWorkflowService`, which are also used directly by the Workflow Engine's
    YouTube production steps."""

    def __init__(
        self,
        review_workflow_service: ReviewWorkflowService,
        media_workflow_service: MediaWorkflowService,
        publishing_package_workflow_service: PublishingPackageWorkflowService,
    ) -> None:
        self._review = review_workflow_service
        self._media = media_workflow_service
        self._publishing_package = publishing_package_workflow_service

    async def execute(self, script_draft: ScriptDraft, user_id: str | None) -> PublishingPackage:
        reviewed_script = await self._review.execute(script_draft, user_id)
        media_package = await self._media.execute(reviewed_script, user_id)
        return await self._publishing_package.execute(reviewed_script, media_package, user_id)
