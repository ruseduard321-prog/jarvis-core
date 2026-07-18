from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

from backend.core.metrics import get_metrics_provider

router = APIRouter()


@router.get("/metrics", response_class=PlainTextResponse)
async def metrics() -> PlainTextResponse:
    return PlainTextResponse(get_metrics_provider().collect(), media_type="text/plain; version=0.0.4")
