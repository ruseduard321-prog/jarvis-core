from __future__ import annotations

from backend.models.agent import Agent
from backend.repositories.agent_repository import AgentRepository


class AgentService:
    """Service layer for persistent agent entities."""

    DEFAULT_AGENT_SLUG = "general"

    def __init__(self, repository: AgentRepository) -> None:
        self._repository = repository

    async def list_agents(self, owner_user_id: str | None = None, active_only: bool = True) -> list[Agent]:
        return await self._repository.list_agents(owner_user_id=owner_user_id, active_only=active_only)

    async def get_default_agent(self) -> Agent | None:
        """Resolve the seeded General Assistant used when a chat request has no explicit agent_id."""
        try:
            candidate = await self._repository.get_agent(self.DEFAULT_AGENT_SLUG)
            if candidate.is_active:
                return candidate
        except Exception:
            pass

        try:
            agents = await self._repository.list_agents(active_only=True)
        except Exception:
            return None

        for agent in agents:
            if agent.slug == self.DEFAULT_AGENT_SLUG:
                return agent
        return None

    async def get_agent(self, agent_id: str) -> Agent:
        return await self._repository.get_agent(agent_id)

    async def create_agent(
        self,
        owner_user_id: str,
        slug: str,
        name: str,
        mission: str,
        allowed_delegations: list[str] | None = None,
    ) -> Agent:
        return await self._repository.create_agent(
            owner_user_id=owner_user_id,
            slug=slug,
            name=name,
            mission=mission,
            allowed_delegations=allowed_delegations,
        )

    async def update_agent(
        self,
        agent_id: str,
        slug: str | None = None,
        name: str | None = None,
        mission: str | None = None,
        allowed_delegations: list[str] | None = None,
        is_active: bool | None = None,
    ) -> Agent:
        return await self._repository.update_agent(
            agent_id=agent_id,
            slug=slug,
            name=name,
            mission=mission,
            allowed_delegations=allowed_delegations,
            is_active=is_active,
        )

    async def seed_core_business_agents(self, owner_user_id: str = "system") -> list[Agent]:
        return await self._repository.seed_core_business_agents(owner_user_id=owner_user_id)
