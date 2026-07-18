from fastapi import APIRouter

from backend.api.v1.auth import router as auth_router
from backend.api.v1.health import router as health_router
from backend.api.v1.metrics import router as metrics_router
from backend.api.v1.projects import router as projects_router
from backend.api.v1.users import router as users_router
from backend.api.v1.conversations import router as conversations_router
from backend.api.v1.knowledge import router as knowledge_router
from backend.api.v1.execution import router as execution_router
from backend.api.v1.documents import router as documents_router

router = APIRouter()
router.include_router(health_router, prefix="")
router.include_router(metrics_router, prefix="")
router.include_router(projects_router, prefix="")
router.include_router(users_router, prefix="")
router.include_router(auth_router, prefix="")
router.include_router(conversations_router, prefix="")
router.include_router(knowledge_router, prefix="")
router.include_router(execution_router, prefix="")
router.include_router(documents_router, prefix="")
