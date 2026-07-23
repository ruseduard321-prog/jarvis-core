from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from backend.api.dependencies.security import get_current_user
from backend.auth.auth_models import AuthUser
from backend.core.dependencies import get_agent_service
from backend.core.domain_exceptions import ResourceNotFoundError
from backend.schemas.agent import AgentCreateRequest, AgentResponse, AgentUpdateRequest

router = APIRouter(prefix="/agents", tags=["agents"])


@router.get("", response_model=list[AgentResponse])
async def list_agents(
    current_user: AuthUser = Depends(get_current_user),
    agent_service=Depends(get_agent_service),
) -> list[AgentResponse]:
    """List active agents owned by the current user plus seeded system agents."""
    try:
        owned = await agent_service.list_agents(owner_user_id=current_user.id, active_only=True)
        system = await agent_service.list_agents(owner_user_id="system", active_only=True)

        merged = {agent.id: agent for agent in [*system, *owned]}
        return [AgentResponse(**agent.model_dump()) for agent in merged.values()]
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: str,
    current_user: AuthUser = Depends(get_current_user),
    agent_service=Depends(get_agent_service),
) -> AgentResponse:
    """Get one agent if owned by current user or system-owned."""
    try:
        agent = await agent_service.get_agent(agent_id)
        if agent.owner_user_id not in {"system", current_user.id}:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        return AgentResponse(**agent.model_dump())
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("", response_model=AgentResponse, status_code=status.HTTP_201_CREATED)
async def create_agent(
    request: AgentCreateRequest,
    current_user: AuthUser = Depends(get_current_user),
    agent_service=Depends(get_agent_service),
) -> AgentResponse:
    """Create a new agent owned by the current user."""
    try:
        agent = await agent_service.create_agent(
            owner_user_id=current_user.id,
            slug=request.slug,
            name=request.name,
            mission=request.mission,
            allowed_delegations=request.allowed_delegations,
        )
        return AgentResponse(**agent.model_dump())
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.patch("/{agent_id}", response_model=AgentResponse)
async def update_agent(
    agent_id: str,
    request: AgentUpdateRequest,
    current_user: AuthUser = Depends(get_current_user),
    agent_service=Depends(get_agent_service),
) -> AgentResponse:
    """Update an owned agent (system agents are immutable)."""
    try:
        existing = await agent_service.get_agent(agent_id)
        if existing.owner_user_id == "system":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="System agent is read-only")
        if existing.owner_user_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

        updated = await agent_service.update_agent(
            agent_id=agent_id,
            slug=request.slug,
            name=request.name,
            mission=request.mission,
            allowed_delegations=request.allowed_delegations,
            is_active=request.is_active,
        )
        return AgentResponse(**updated.model_dump())
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
