from __future__ import annotations

import logging
import time
import uuid
from datetime import datetime
from typing import Any, AsyncIterator

from backend.core.agent_orchestration_models import AgentResult, ExecutionContext
from backend.core.agent_orchestrator import AgentOrchestrator
from backend.core.conversation_engine import ConversationEngine
from backend.core.conversation_models import ConversationMessage, ConversationRole

logger = logging.getLogger(__name__)


class AgentRuntime:
    """Runtime orchestration backbone for agent-based execution."""

    def __init__(
        self,
        conversation_engine: ConversationEngine,
        agent_orchestrator: AgentOrchestrator,
    ) -> None:
        self._conversation_engine = conversation_engine
        self._agent_orchestrator = agent_orchestrator

    async def _start_execution(
        self,
        conversation_id: str,
        agent_id: str,
        message: str,
        user_id: str | None,
        temperature: float | None,
        max_tokens: int | None,
        metadata: dict[str, Any] | None,
    ) -> tuple[str, ConversationMessage, ExecutionContext]:
        """Persist the user's message and build the execution context. Shared by both
        `execute()` and `stream_execute()` so the two can't drift out of sync."""
        execution_id = str(uuid.uuid4())
        safe_metadata = metadata or {}

        user_message = ConversationMessage(
            id=str(uuid.uuid4()),
            role=ConversationRole.USER,
            content=message,
            created_at=datetime.utcnow(),
            metadata={**safe_metadata, "agent_id": agent_id, "execution_id": execution_id},
        )
        await self._conversation_engine.append_message(conversation_id, user_message)

        execution_context = ExecutionContext(
            conversation_id=conversation_id,
            user_id=user_id,
            memory=safe_metadata.get("memory", []) if isinstance(safe_metadata.get("memory"), list) else [],
            documents=safe_metadata.get("documents", []) if isinstance(safe_metadata.get("documents"), list) else [],
            media_assets=safe_metadata.get("media_assets", []) if isinstance(safe_metadata.get("media_assets"), list) else [],
            artifacts=safe_metadata.get("artifacts", []) if isinstance(safe_metadata.get("artifacts"), list) else [],
            execution_depth=0,
            metadata={
                **safe_metadata,
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
        )
        return execution_id, user_message, execution_context

    async def _persist_assistant_message(
        self,
        conversation_id: str,
        agent_id: str,
        execution_id: str,
        orchestrated: AgentResult,
    ) -> tuple[str, ConversationMessage]:
        """Build and persist the assistant message from a completed orchestration result.
        Shared by both `execute()` and `stream_execute()`."""
        output_payload = orchestrated.output if isinstance(orchestrated.output, dict) else {}
        output = str(output_payload.get("text") or orchestrated.summary)

        assistant_message = ConversationMessage(
            id=str(uuid.uuid4()),
            role=ConversationRole.ASSISTANT,
            content=output,
            created_at=datetime.utcnow(),
            metadata={
                "agent_id": agent_id,
                "execution_id": execution_id,
                "orchestrator": {
                    "tool_calls": orchestrated.tool_calls,
                    "delegated_agents": orchestrated.delegated_agents,
                    "metadata": orchestrated.metadata,
                },
            },
        )
        await self._conversation_engine.append_message(conversation_id, assistant_message)
        return output, assistant_message

    async def execute(
        self,
        conversation_id: str,
        agent_id: str,
        message: str,
        user_id: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Execute one agent turn and persist conversation messages."""
        start_time = time.perf_counter()

        execution_id, user_message, execution_context = await self._start_execution(
            conversation_id, agent_id, message, user_id, temperature, max_tokens, metadata
        )

        orchestrated = await self._agent_orchestrator.execute(
            agent_id=agent_id,
            objective=message,
            context=execution_context,
        )

        output, assistant_message = await self._persist_assistant_message(
            conversation_id, agent_id, execution_id, orchestrated
        )

        elapsed_ms = int((time.perf_counter() - start_time) * 1000)
        logger.info(
            "agent_execution_completed",
            extra={
                "conversation_id": conversation_id,
                "selected_agent": agent_id,
                "delegated_agents": [
                    item.get("target_agent") for item in orchestrated.delegated_agents
                ],
                "tools_used": [call.get("tool") for call in orchestrated.tool_calls if call.get("tool")],
                "execution_time_ms": elapsed_ms,
                "final_status": orchestrated.status,
            },
        )

        return {
            "execution_id": execution_id,
            "user_message_id": user_message.id,
            "assistant_message_id": assistant_message.id,
            "content": output,
            "agent_id": agent_id,
            "status": orchestrated.status,
            "tool_calls": orchestrated.tool_calls,
            "delegated_agents": orchestrated.delegated_agents,
        }

    async def stream_execute(
        self,
        conversation_id: str,
        agent_id: str,
        message: str,
        user_id: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> AsyncIterator[dict[str, str]]:
        """Execute one agent turn with true incremental streaming.

        Consumes `AgentOrchestrator.stream_execute()` directly (never calls `execute()`
        first), forwarding each delta to the caller the moment it arrives. The assistant
        message is persisted only after the orchestrator's stream yields its final result.
        """
        start_time = time.perf_counter()

        execution_id, user_message, execution_context = await self._start_execution(
            conversation_id, agent_id, message, user_id, temperature, max_tokens, metadata
        )

        yield {"event": "start", "message_id": user_message.id}

        orchestrated: AgentResult | None = None
        async for event in self._agent_orchestrator.stream_execute(
            agent_id=agent_id,
            objective=message,
            context=execution_context,
        ):
            if event["type"] == "delta":
                if event["text"]:
                    yield {"event": "token", "data": event["text"]}
            else:
                orchestrated = event["result"]

        if orchestrated is None:
            raise RuntimeError("agent orchestrator stream ended without yielding a final result")

        _, assistant_message = await self._persist_assistant_message(
            conversation_id, agent_id, execution_id, orchestrated
        )

        elapsed_ms = int((time.perf_counter() - start_time) * 1000)
        logger.info(
            "agent_execution_completed",
            extra={
                "conversation_id": conversation_id,
                "selected_agent": agent_id,
                "delegated_agents": [
                    item.get("target_agent") for item in orchestrated.delegated_agents
                ],
                "tools_used": [call.get("tool") for call in orchestrated.tool_calls if call.get("tool")],
                "execution_time_ms": elapsed_ms,
                "final_status": orchestrated.status,
            },
        )

        yield {"event": "end", "message_id": assistant_message.id}
