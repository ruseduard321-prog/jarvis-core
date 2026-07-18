from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from backend.core.health import (
    AppHealthInfo,
    HealthStatus,
    build_health_info,
    check_auth,
    check_database,
    check_storage,
    format_overall_status,
    run_health_checks,
)
from backend.schemas.health import AppHealthResponse, LivenessResponse, ReadinessResponse

router = APIRouter()


@router.get("/health/live", response_model=LivenessResponse)
async def health_liveness() -> LivenessResponse:
    return LivenessResponse(status="alive")


@router.get("/health/ready", response_model=ReadinessResponse)
async def health_readiness() -> JSONResponse:
    checks = await run_health_checks([check_database, check_auth, check_storage])
    results = {check.message or "unknown": check.healthy for check in checks}
    overall_status = format_overall_status(checks)
    status_code = status.HTTP_200_OK if overall_status == "ok" else status.HTTP_503_SERVICE_UNAVAILABLE
    return JSONResponse(
        status_code=status_code,
        content=ReadinessResponse(status=overall_status, checks=results).model_dump(),
    )


@router.get("/health", response_model=AppHealthResponse)
async def health_check() -> AppHealthResponse:
    health_info = build_health_info()
    return AppHealthResponse(
        service=health_info.service,
        version=health_info.version,
        environment=health_info.environment,
        uptime_seconds=health_info.uptime_seconds,
        status=health_info.status,
    )
