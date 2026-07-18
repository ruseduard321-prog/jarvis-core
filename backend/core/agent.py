from __future__ import annotations

import abc
from typing import Any

from backend.core.agent_models import AgentContext, AgentResponse


class Agent(abc.ABC):
    """Abstract interface for AI agents."""

    @property
    @abc.abstractmethod
    def id(self) -> str:
        """Return the agent ID."""
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def name(self) -> str:
        """Return the agent name."""
        raise NotImplementedError

    @abc.abstractmethod
    async def execute(self, message: str, context: AgentContext) -> AgentResponse:
        """Execute the agent with a message and context."""
        raise NotImplementedError


class AgentRegistry:
    """Registry for managing agents."""

    def __init__(self) -> None:
        self._agents: dict[str, Agent] = {}

    def register(self, agent: Agent) -> None:
        """Register an agent by ID."""
        self._agents[agent.id] = agent

    def unregister(self, agent_id: str) -> None:
        """Unregister an agent by ID."""
        if agent_id in self._agents:
            del self._agents[agent_id]

    def get(self, agent_id: str) -> Agent:
        """Get a registered agent by ID."""
        if agent_id not in self._agents:
            raise ValueError(f"Agent not registered: {agent_id}")
        return self._agents[agent_id]

    def list_agents(self) -> list[tuple[str, str]]:
        """List all registered agents as (id, name) tuples."""
        return [(agent.id, agent.name) for agent in self._agents.values()]
