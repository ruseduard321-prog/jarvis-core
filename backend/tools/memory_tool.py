from __future__ import annotations

from typing import Any

from backend.core.memory_models import MemoryMetadata, MemoryQuery, MemoryRecord
from backend.core.memory_service import MemoryService
from backend.core.tool import Tool
from backend.core.tool_models import ToolContext, ToolResult


class MemoryTool(Tool):
    """Generic memory read/write tool backed by MemoryService."""

    def __init__(self, memory_service: MemoryService) -> None:
        self._memory_service = memory_service

    @property
    def slug(self) -> str:
        return "memory"

    @property
    def name(self) -> str:
        return "Memory Tool"

    @property
    def description(self) -> str:
        return "Read and write memory records using MemoryService."

    @property
    def capabilities(self) -> list[str]:
        return ["memory.read", "memory.write", "memory.search"]

    async def execute(self, args: dict[str, Any], context: ToolContext) -> ToolResult:
        action = str(args.get("action", "")).lower()

        if action == "list":
            limit = int(args.get("limit", 20))
            offset = int(args.get("offset", 0))
            result = await self._memory_service.list_memory(limit=limit, offset=offset)
            return ToolResult(success=True, output=self._serialize_result(result.records, result.total_count))

        if action == "get":
            memory_id = str(args.get("memory_id", "")).strip()
            if not memory_id:
                return ToolResult(success=False, error="Missing required argument: memory_id")
            record = await self._memory_service.get_memory(memory_id)
            return ToolResult(success=True, output=self._serialize_record(record))

        if action == "create":
            record_type = str(args.get("record_type", "")).strip()
            content = str(args.get("content", "")).strip()
            if not record_type:
                return ToolResult(success=False, error="Missing required argument: record_type")
            if not content:
                return ToolResult(success=False, error="Missing required argument: content")

            metadata = self._build_metadata(args, context)
            record = await self._memory_service.create_memory(
                record_type=record_type,
                content=content,
                metadata=metadata,
            )
            return ToolResult(success=True, output=self._serialize_record(record))

        if action == "update":
            memory_id = str(args.get("memory_id", "")).strip()
            if not memory_id:
                return ToolResult(success=False, error="Missing required argument: memory_id")

            content = args.get("content")
            metadata = self._build_metadata(args, context, allow_empty=True)
            record = await self._memory_service.update_memory(
                memory_id=memory_id,
                content=content,
                metadata=metadata,
            )
            return ToolResult(success=True, output=self._serialize_record(record))

        if action == "delete":
            memory_id = str(args.get("memory_id", "")).strip()
            if not memory_id:
                return ToolResult(success=False, error="Missing required argument: memory_id")
            await self._memory_service.delete_memory(memory_id)
            return ToolResult(success=True, output={"deleted": True, "memory_id": memory_id})

        if action == "query":
            query = MemoryQuery(
                record_type=args.get("record_type"),
                source=args.get("source"),
                tags=args.get("tags"),
                metadata_filters=args.get("metadata_filters"),
                limit=args.get("limit"),
                offset=args.get("offset"),
            )
            result = await self._memory_service.query_memory(query)
            return ToolResult(success=True, output=self._serialize_result(result.records, result.total_count))

        return ToolResult(
            success=False,
            error="Invalid action. Supported actions: list, get, create, update, delete, query",
        )

    def _build_metadata(
        self,
        args: dict[str, Any],
        context: ToolContext,
        allow_empty: bool = False,
    ) -> MemoryMetadata | None:
        source = args.get("source")
        tags = args.get("tags")
        attributes = dict(args.get("attributes") or {})

        if context.user_id and "user_id" not in attributes:
            attributes["user_id"] = context.user_id
        if context.agent_id and "agent_id" not in attributes:
            attributes["agent_id"] = context.agent_id
        if context.conversation_id and "conversation_id" not in attributes:
            attributes["conversation_id"] = context.conversation_id

        if allow_empty and source is None and tags is None and not attributes:
            return None

        return MemoryMetadata(
            source=source,
            tags=list(tags or []),
            attributes=attributes,
        )

    def _serialize_record(self, record: MemoryRecord) -> dict[str, Any]:
        return {
            "id": record.id,
            "record_type": record.record_type,
            "content": record.content,
            "metadata": {
                "source": record.metadata.source,
                "tags": record.metadata.tags,
                "attributes": record.metadata.attributes,
            },
            "created_at": record.created_at.isoformat(),
            "updated_at": record.updated_at.isoformat(),
        }

    def _serialize_result(self, records: list[MemoryRecord], total_count: int) -> dict[str, Any]:
        return {
            "records": [self._serialize_record(record) for record in records],
            "total_count": total_count,
        }
