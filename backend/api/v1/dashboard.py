"""Dashboard API endpoints."""

from fastapi import APIRouter, Depends

from backend.core.dependencies import get_dashboard_service
from backend.services.dashboard_service import DashboardService
from backend.schemas.dashboard import DashboardResponse

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("", response_model=DashboardResponse)
async def get_dashboard(
    service: DashboardService = Depends(get_dashboard_service),
) -> DashboardResponse:
    """Get complete dashboard data."""
    return await service.get_dashboard()
