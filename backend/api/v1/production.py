from __future__ import annotations

import asyncio
import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, status

from backend.api.dependencies.security import get_current_user
from backend.auth.auth_models import AuthUser
from backend.core.dependencies import (
    get_task_manager,
    get_workflow_engine,
    get_workflow_history_store,
    get_youtube_production_workflow_definition,
)
from backend.core.task_manager import BackgroundTaskManager
from backend.core.workflow_engine import WorkflowEngine
from backend.core.workflow_engine_models import WorkflowDefinition
from backend.core.workflow_history_store import WorkflowHistoryRecord, WorkflowHistoryStore
from backend.schemas.production import ProductionRunRequest, ProductionRunResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/production", tags=["production"])

# F1: production runs are dispatched as background tasks of this type, tracked
# through the existing BackgroundTaskManager/TaskBackend infrastructure.
PRODUCTION_RUN_TASK_TYPE = "youtube_production_run"

# F1: asyncio.create_task() does not itself keep the task alive — without a
# strong reference the task object can be garbage-collected mid-execution (a
# well-documented asyncio gotcha). This module-level set is that reference; each
# task removes itself on completion via its done-callback.
_background_tasks: set[asyncio.Task] = set()


def _track_background_task(task: asyncio.Task) -> None:
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)


@router.post("/runs", response_model=ProductionRunResponse, status_code=status.HTTP_202_ACCEPTED)
async def start_production_run(
    request: ProductionRunRequest,
    current_user: AuthUser = Depends(get_current_user),
    workflow_engine: WorkflowEngine = Depends(get_workflow_engine),
    workflow_definition: WorkflowDefinition = Depends(get_youtube_production_workflow_definition),
    task_manager: BackgroundTaskManager = Depends(get_task_manager),
) -> ProductionRunResponse:
    """F1: triggers a full YouTube production pipeline run and returns
    IMMEDIATELY with its execution_id — the run itself executes in the
    background via BackgroundTaskManager/asyncio, never blocking this request.
    Poll GET /production/runs/{execution_id} for progress/status/results."""
    task = await task_manager.submit(PRODUCTION_RUN_TASK_TYPE, {"topic": request.topic, "user_id": current_user.id})

    background_task = asyncio.create_task(
        _run_production_in_background(
            workflow_engine=workflow_engine,
            workflow_definition=workflow_definition,
            task_manager=task_manager,
            execution_id=task.id,
            topic=request.topic,
            user_id=current_user.id,
        )
    )
    _track_background_task(background_task)

    return ProductionRunResponse(execution_id=task.id, status="pending")


@router.get("/runs/{execution_id}", response_model=ProductionRunResponse)
async def get_production_run(
    execution_id: str,
    current_user: AuthUser = Depends(get_current_user),
    task_manager: BackgroundTaskManager = Depends(get_task_manager),
    history_store: WorkflowHistoryStore = Depends(get_workflow_history_store),
) -> ProductionRunResponse:
    """F1: retrieves progress/status/results for a production run started via
    POST /production/runs, independent of whether it has finished yet."""
    record = await history_store.get(execution_id)
    if record is not None:
        return _response_from_history_record(execution_id, record)

    # The workflow hasn't started recording history yet (a brief window right
    # after submission, before the background task's first await point) — fall
    # back to the task-level record, which exists from the moment submit() runs.
    task = await task_manager.get(execution_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Production run not found: {execution_id}")

    return ProductionRunResponse(execution_id=execution_id, status="pending")


async def _run_production_in_background(
    *,
    workflow_engine: WorkflowEngine,
    workflow_definition: WorkflowDefinition,
    task_manager: BackgroundTaskManager,
    execution_id: str,
    topic: str,
    user_id: str,
) -> None:
    """F1: the actual pipeline execution, run outside the request/response cycle.
    Mirrors the exact stream_execute call the old synchronous endpoint made —
    only the caller (a background task instead of an HTTP handler) changed."""
    await task_manager.mark_started(execution_id)
    succeeded = False
    try:
        conversation_id = str(uuid.uuid4())
        final_result: dict[str, object] = {}
        async for event in workflow_engine.stream_execute(
            workflow_definition,
            topic=topic,
            conversation_id=conversation_id,
            user_id=user_id,
            execution_id=execution_id,
        ):
            if event["type"] == "result":
                final_result = event["result"]
        succeeded = final_result.get("status") == "success"
    except Exception:
        logger.exception("production_run_background_task_failed", extra={"execution_id": execution_id})
        succeeded = False
    finally:
        await task_manager.mark_finished(execution_id, succeeded=succeeded)


def _response_from_history_record(execution_id: str, record: WorkflowHistoryRecord) -> ProductionRunResponse:
    step_statuses = {name: "success" for name in record.steps_executed}
    if record.failed_step:
        step_statuses[record.failed_step] = "failed"
    return ProductionRunResponse(
        execution_id=execution_id,
        status=record.status,
        output_folder=record.output_folder,
        files_written=record.artifacts_generated,
        step_statuses=step_statuses,
        failed_step=record.failed_step,
        error=f"Step '{record.failed_step}' failed" if record.failed_step else None,
    )
