from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from backend.core.agent import Agent, AgentRegistry
from backend.core.agent_models import AgentContext, AgentExecution, AgentResponse, AgentSession, AgentStatus
from backend.core.event_bus_service import EventBusService
from backend.core.retrieval_engine import RetrievalEngine
from backend.core.tool_executor import ToolExecutor
from backend.core.vector_service import VectorService
from backend.core.memory_service import MemoryService
from backend.core.conversation_engine import ConversationEngine


class AgentRuntime:
    """Runtime for executing agents with context management."""

    def __init__(
        self,
        agent_registry: AgentRegistry,
        tool_executor: ToolExecutor,
        retrieval_engine: RetrievalEngine,
        event_bus_service: EventBusService,
    ) -> None:
        self._agent_registry = agent_registry
        self._tool_executor = tool_executor
        self._retrieval_engine = retrieval_engine
        self._event_bus_service = event_bus_service
        self._executions: dict[str, AgentExecution] = {}

    async def run_agent(
        self,
        agent_id: str,
        message: str,
        context: AgentContext,
    ) -> AgentResponse:
        """Execute an agent with full context."""
        execution_id = str(uuid.uuid4())
        
        try:
            agent = self._agent_registry.get(agent_id)
        except ValueError as e:
            return AgentResponse(
                agent_id=agent_id,
                status=AgentStatus.FAILED,
                message=f"Agent not found: {agent_id}",
            )

        await self._event_bus_service.publish_event(
            "AgentStarted",
            payload={"agent_id": agent_id, "execution_id": execution_id},
            metadata={"agent_id": agent_id},
        )

        execution = AgentExecution(
            agent_id=agent_id,
            execution_id=execution_id,
            status=AgentStatus.RUNNING,
            input_message=message,
            started_at=datetime.utcnow(),
        )
        self._executions[execution_id] = execution

        try:
            response = await agent.execute(message, context)
            
            execution = AgentExecution(
                agent_id=execution.agent_id,
                execution_id=execution.execution_id,
                status=response.status,
                input_message=execution.input_message,
                output_message=response.message,
                completed_at=datetime.utcnow(),
            )
            self._executions[execution_id] = execution

            await self._event_bus_service.publish_event(
                "AgentFinished",
                payload={
                    "agent_id": agent_id,
                    "execution_id": execution_id,
                    "status": response.status.value,
                },
                metadata={"agent_id": agent_id},
            )

            return response

        except Exception as e:
            execution = AgentExecution(
                agent_id=execution.agent_id,
                execution_id=execution.execution_id,
                status=AgentStatus.FAILED,
                input_message=execution.input_message,
                completed_at=datetime.utcnow(),
            )
            self._executions[execution_id] = execution

            await self._event_bus_service.publish_event(
                "AgentFinished",
                payload={
                    "agent_id": agent_id,
                    "execution_id": execution_id,
                    "status": AgentStatus.FAILED.value,
                    "error": str(e),
                },
                metadata={"agent_id": agent_id},
            )

            return AgentResponse(
                agent_id=agent_id,
                status=AgentStatus.FAILED,
                message=f"Agent execution failed: {str(e)}",
                execution_id=execution_id,
            )

    def get_execution(self, execution_id: str) -> AgentExecution | None:
        """Get execution trace by ID."""
        return self._executions.get(execution_id)
