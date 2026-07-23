from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
import uuid
import time
from datetime import datetime

from backend.schemas.execution import (
    WorkflowDefinitionRequest,
    WorkflowExecutionRequest,
    WorkflowExecutionResponse,
    WorkflowStatus,
)

router = APIRouter(tags=["execution", "workflows"])


# ============================================================
# WORKFLOW ENDPOINTS
# ============================================================

workflows_db: dict[str, dict] = {}  # Temporary in-memory storage


@router.post("/workflows", status_code=status.HTTP_201_CREATED)
async def create_workflow(
    request: WorkflowDefinitionRequest,
) -> dict:
    """Create a workflow."""
    try:
        workflow_id = str(uuid.uuid4())
        workflows_db[workflow_id] = {
            "id": workflow_id,
            "name": request.name,
            "description": request.description,
            "nodes": request.nodes,
            "edges": request.edges,
            "metadata": request.metadata,
            "created_at": datetime.utcnow().isoformat(),
        }
        
        return {
            "id": workflow_id,
            "name": request.name,
            "created_at": datetime.utcnow().isoformat(),
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get("/workflows/{workflow_id}")
async def get_workflow(
    workflow_id: str,
) -> dict:
    """Get workflow definition."""
    if workflow_id not in workflows_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow not found: {workflow_id}",
        )
    
    return workflows_db[workflow_id]


@router.post("/workflows/{workflow_id}/execute", response_model=WorkflowExecutionResponse)
async def execute_workflow(
    workflow_id: str,
    request: WorkflowExecutionRequest,
) -> WorkflowExecutionResponse:
    """Execute a workflow."""
    try:
        if workflow_id not in workflows_db:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workflow not found: {workflow_id}",
            )
        
        start_time = time.time()
        duration_ms = int((time.time() - start_time) * 1000)
        
        return WorkflowExecutionResponse(
            workflow_id=workflow_id,
            execution_id=str(uuid.uuid4()),
            status=WorkflowStatus.COMPLETED,
            output_data={"status": "completed"},
            duration_ms=duration_ms,
            metadata={},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
