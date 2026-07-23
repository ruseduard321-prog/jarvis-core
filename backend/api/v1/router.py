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
from backend.api.v1.dashboard import router as dashboard_router
from backend.api.v1.prompts import router as prompts_router
from backend.api.v1.agents import router as agents_router
from backend.api.v1.tools import router as tools_router
from backend.api.v1.research import router as research_router
from backend.api.v1.publishing import router as publishing_router
from backend.api.v1.production import router as production_router

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
router.include_router(dashboard_router, prefix="")
router.include_router(prompts_router, prefix="")
router.include_router(agents_router, prefix="")
router.include_router(tools_router, prefix="")
router.include_router(research_router, prefix="")
router.include_router(publishing_router, prefix="")
router.include_router(production_router, prefix="")
