from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
import uuid
import json
import time
from datetime import datetime

from backend.core.dependencies import (
    get_tool_registry,
    get_tool_executor,
    get_agent_registry,
    get_agent_runtime,
)
from backend.schemas.execution import (
    ToolParameterType,
    ToolParameter,
    ToolMetadataResponse,
    ToolExecutionRequest,
    ToolExecutionResponse,
    AgentMetadataResponse,
    AgentStatus,
    AgentExecutionRequest,
    AgentExecutionResponse,
    WorkflowDefinitionRequest,
    WorkflowExecutionRequest,
    WorkflowExecutionResponse,
    WorkflowStatus,
)

router = APIRouter(tags=["execution", "tools", "agents", "workflows"])


# ============================================================
# TOOL ENDPOINTS
# ============================================================

@router.get("/tools", response_model=list[ToolMetadataResponse])
async def list_tools(
    category: str | None = None,
    tool_registry=Depends(get_tool_registry),
) -> list[ToolMetadataResponse]:
    """List available tools."""
    try:
        tools = tool_registry.list_tools()
        
        results = []
        for tool in tools:
            if category and tool.metadata.category != category:
                continue
                
            params = [
                ToolParameter(
                    name=p.name,
                    type=ToolParameterType(p.type),
                    description=p.description,
                    required=p.required,
                    default=p.default,
                )
                for p in tool.metadata.parameters
            ]
            
            results.append(
                ToolMetadataResponse(
                    id=tool.metadata.id,
                    name=tool.metadata.name,
                    description=tool.metadata.description,
                    category=tool.metadata.category,
                    parameters=params,
                    tags=tool.metadata.tags,
                )
            )
        
        return results
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get("/tools/{tool_id}", response_model=ToolMetadataResponse)
async def get_tool(
    tool_id: str,
    tool_registry=Depends(get_tool_registry),
) -> ToolMetadataResponse:
    """Get tool metadata."""
    try:
        tool = tool_registry.get(tool_id)
        
        params = [
            ToolParameter(
                name=p.name,
                type=ToolParameterType(p.type),
                description=p.description,
                required=p.required,
                default=p.default,
            )
            for p in tool.metadata.parameters
        ]
        
        return ToolMetadataResponse(
            id=tool.metadata.id,
            name=tool.metadata.name,
            description=tool.metadata.description,
            category=tool.metadata.category,
            parameters=params,
            tags=tool.metadata.tags,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tool not found: {tool_id}",
        )


@router.post("/tools/{tool_id}/execute", response_model=ToolExecutionResponse)
async def execute_tool(
    tool_id: str,
    request: ToolExecutionRequest,
    tool_executor=Depends(get_tool_executor),
) -> ToolExecutionResponse:
    """Execute a tool."""
    try:
        start_time = time.time()
        
        # Execute tool
        result = await tool_executor.execute(
            tool_id=tool_id,
            arguments=request.arguments,
            timeout_seconds=request.timeout_seconds or 30,
        )
        
        duration_ms = int((time.time() - start_time) * 1000)
        
        return ToolExecutionResponse(
            tool_id=tool_id,
            execution_id=str(uuid.uuid4()),
            status=result.status,
            output=result.output,
            duration_ms=duration_ms,
            metadata=result.metadata,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


# ============================================================
# AGENT ENDPOINTS
# ============================================================

@router.get("/agents", response_model=list[AgentMetadataResponse])
async def list_agents(
    agent_registry=Depends(get_agent_registry),
) -> list[AgentMetadataResponse]:
    """List available agents."""
    try:
        agents = agent_registry.list_agents()
        
        return [
            AgentMetadataResponse(
                id=agent.id,
                name=agent.name,
                description="Agent description",
                capabilities=["reasoning", "planning"],
                tools=[],
                status=AgentStatus.IDLE,
                metadata={},
            )
            for agent in agents
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get("/agents/{agent_id}", response_model=AgentMetadataResponse)
async def get_agent(
    agent_id: str,
    agent_registry=Depends(get_agent_registry),
) -> AgentMetadataResponse:
    """Get agent metadata."""
    try:
        agent = agent_registry.get(agent_id)
        
        return AgentMetadataResponse(
            id=agent.id,
            name=agent.name,
            description="Agent description",
            capabilities=["reasoning", "planning"],
            tools=[],
            status=AgentStatus.IDLE,
            metadata={},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent not found: {agent_id}",
        )


@router.post("/agents/{agent_id}/execute", response_model=AgentExecutionResponse)
async def execute_agent(
    agent_id: str,
    request: AgentExecutionRequest,
    agent_runtime=Depends(get_agent_runtime),
) -> AgentExecutionResponse:
    """Execute an agent."""
    try:
        start_time = time.time()
        
        # Execute agent
        response = await agent_runtime.execute(
            agent_id=agent_id,
            message=request.message,
        )
        
        duration_ms = int((time.time() - start_time) * 1000)
        
        return AgentExecutionResponse(
            agent_id=agent_id,
            execution_id=str(uuid.uuid4()),
            status=AgentStatus.COMPLETED,
            response=response.response,
            tools_used=[],
            duration_ms=duration_ms,
            metadata={},
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.post("/agents/{agent_id}/execute/stream")
async def execute_agent_stream(
    agent_id: str,
    request: AgentExecutionRequest,
    agent_runtime=Depends(get_agent_runtime),
):
    """Execute an agent with streaming response."""
    
    async def event_generator():
        try:
            execution_id = str(uuid.uuid4())
            
            # Send start event
            yield f"data: {json.dumps({'event': 'start', 'execution_id': execution_id})}\n\n"
            
            # Execute agent (in real implementation, would stream)
            response = await agent_runtime.execute(
                agent_id=agent_id,
                message=request.message,
            )
            
            # Stream response tokens
            for token in response.response.split():
                yield f"data: {json.dumps({'event': 'token', 'data': token + ' '})}\n\n"
            
            # Send end event
            yield f"data: {json.dumps({'event': 'end', 'execution_id': execution_id})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'event': 'error', 'data': str(e)})}\n\n"
    
    return StreamingResponse(event_generator(), media_type="text/event-stream")


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
