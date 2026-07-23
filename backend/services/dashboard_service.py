"""Dashboard service for aggregating platform data."""

import logging
from datetime import datetime

from backend.core.agent_registry_provider import agent_registry
from backend.core.conversation_store import ConversationStore
from backend.core.memory_store import MemoryStore
from backend.core.event_bus_service import EventBusService
from backend.core.memory_models import MemoryQuery
from backend.schemas.dashboard import (
    ActivityEvent,
    ConversationSummary,
    DashboardResponse,
    QuickAction,
    Statistics,
    StatusIndicator,
    SystemStatus,
)

logger = logging.getLogger(__name__)


class DashboardService:
    """Service for aggregating dashboard data from all sources."""

    def __init__(
        self,
        conversation_store: ConversationStore,
        memory_store: MemoryStore,
        event_bus_service: EventBusService,
    ) -> None:
        self.conversation_store = conversation_store
        self.memory_store = memory_store
        self.event_bus_service = event_bus_service

    async def get_dashboard(self) -> DashboardResponse:
        """Get complete dashboard state."""
        stats = await self._get_statistics()
        conversations = await self._get_recent_conversations()
        activity = await self._get_activity()
        system_status = await self._get_system_status()
        quick_actions = self._get_quick_actions()

        return DashboardResponse(
            statistics=stats,
            recent_conversations=conversations,
            activity=activity,
            system_status=system_status,
            quick_actions=quick_actions,
            timestamp=datetime.utcnow(),
        )

    async def _get_statistics(self) -> Statistics:
        """Aggregate statistics from all sources."""
        try:
            # Get all conversations
            conversations = await self.conversation_store.list_conversations()

            total_conversations = len(conversations)
            total_messages = sum(len(conv.messages) for conv in conversations)

            # Get memory items (knowledge base)
            memory_query = MemoryQuery()
            memory_result = await self.memory_store.query_memory(memory_query)
            total_knowledge_items = memory_result.total_count

            # Get agents
            agents_list = agent_registry.list_agents()
            total_agents = len(agents_list)

            # TODO: Connect to real document statistics when Documents module is implemented
            total_documents = 0

            # Calculate today's activity (conversations created today)
            now = datetime.utcnow()
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            today_activity = sum(
                1
                for conv in conversations
                if conv.context.created_at and conv.context.created_at >= today_start
            )

            return Statistics(
                total_conversations=total_conversations,
                total_messages=total_messages,
                total_knowledge_items=total_knowledge_items,
                total_agents=total_agents,
                total_documents=total_documents,
                today_activity=today_activity,
            )
        except Exception as e:
            logger.exception("Error getting statistics")
            return Statistics(
                total_conversations=0,
                total_messages=0,
                total_knowledge_items=0,
                total_agents=0,
                total_documents=0,
                today_activity=0,
            )

    async def _get_recent_conversations(self, limit: int = 10) -> list[ConversationSummary]:
        """Get recent conversations sorted by update time."""
        try:
            conversations = await self.conversation_store.list_conversations()

            # Sort by updated_at descending
            sorted_convs = sorted(
                conversations,
                key=lambda c: c.context.updated_at or datetime.utcnow(),
                reverse=True,
            )

            result = []
            for conv in sorted_convs[:limit]:
                result.append(
                    ConversationSummary(
                        id=conv.context.conversation_id,
                        title=conv.context.title or "Untitled",
                        message_count=len(conv.messages),
                        last_message_at=conv.context.updated_at or datetime.utcnow(),
                        status=conv.context.state.value,
                    )
                )
            return result
        except Exception as e:
            logger.exception("Error getting recent conversations")
            return []

    async def _get_activity(self, limit: int = 15) -> list[ActivityEvent]:
        """Generate activity feed from recent conversations."""
        try:
            conversations = await self.conversation_store.list_conversations()

            # Create activity events from recent conversations and messages
            events: list[tuple[datetime, ActivityEvent]] = []

            for conv in conversations:
                # Add conversation created event
                if conv.context.created_at:
                    event = ActivityEvent(
                        id=f"conv-created-{conv.context.conversation_id}",
                        type="conversation_created",
                        timestamp=conv.context.created_at,
                        description=f"Created conversation: {conv.context.title or 'Untitled'}",
                        metadata={"conversation_id": conv.context.conversation_id},
                    )
                    events.append((conv.context.created_at, event))

                # Add message events (last 3 messages per conversation)
                for msg in conv.messages[-3:]:
                    event = ActivityEvent(
                        id=f"msg-{msg.id}",
                        type="message_sent",
                        timestamp=msg.created_at,
                        description=f"Message in {conv.context.title or 'Untitled'}",
                        metadata={
                            "conversation_id": conv.context.conversation_id,
                            "role": msg.role.value,
                        },
                    )
                    events.append((msg.created_at, event))

            # Sort by timestamp descending, take limit
            events.sort(key=lambda x: x[0], reverse=True)
            return [event for _, event in events[:limit]]
        except Exception as e:
            logger.exception("Error getting activity")
            return []

    async def _get_system_status(self) -> SystemStatus:
        """Check system health indicators."""
        try:
            now = datetime.utcnow()

            # For MVP, assume everything is healthy
            # These can be enhanced with actual health checks
            backend_status = StatusIndicator(
                name="Backend API",
                status="online",
                message="All systems operational",
                timestamp=now,
            )

            database_status = StatusIndicator(
                name="Database",
                status="online",
                message="Connected",
                timestamp=now,
            )

            ai_provider_status = StatusIndicator(
                name="AI Provider",
                status="online",
                message="API responsive",
                timestamp=now,
            )

            return SystemStatus(
                status="healthy",
                backend=backend_status,
                database=database_status,
                ai_provider=ai_provider_status,
                timestamp=now,
            )
        except Exception as e:
            logger.exception("Error getting system status")
            now = datetime.utcnow()
            return SystemStatus(
                status="degraded",
                backend=StatusIndicator(
                    name="Backend API",
                    status="degraded",
                    message=str(e),
                    timestamp=now,
                ),
                database=StatusIndicator(
                    name="Database", status="unknown", message="Unknown", timestamp=now
                ),
                ai_provider=StatusIndicator(
                    name="AI Provider",
                    status="unknown",
                    message="Unknown",
                    timestamp=now,
                ),
                timestamp=now,
            )

    def _get_quick_actions(self) -> list[QuickAction]:
        """Get quick action cards."""
        return [
            QuickAction(
                id="new-chat",
                label="New Chat",
                description="Start a new conversation",
                icon="plus",
                href="/chat",
            ),
            QuickAction(
                id="knowledge-base",
                label="Knowledge Base",
                description="Manage your knowledge",
                icon="book",
                href="/knowledge",
            ),
            QuickAction(
                id="agents",
                label="Agents",
                description="View and manage agents",
                icon="bot",
                href="/agents",
            ),
            QuickAction(
                id="settings",
                label="Settings",
                description="Configure your workspace",
                icon="settings",
                href="/settings",
            ),
        ]
