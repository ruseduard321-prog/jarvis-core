from fastapi import APIRouter

from backend.api.v1.auth import router as auth_router
from backend.api.v1.health import router as health_router
from backend.api.v1.metrics import router as metrics_router
from backend.api.v1.projects import router as projects_router
from backend.api.v1.users import router as users_router

router = APIRouter()
router.include_router(health_router, prefix="")
router.include_router(metrics_router, prefix="")
router.include_router(projects_router, prefix="")
router.include_router(users_router, prefix="")
router.include_router(auth_router, prefix="")
