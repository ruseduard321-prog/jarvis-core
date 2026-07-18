from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class RetrievedContext:
    """Context retrieved from knowledge base."""

    documents: list[dict[str, Any]] = field(default_factory=list)
    vectors: list[dict[str, Any]] = field(default_factory=list)
    memory_records: list[dict[str, Any]] = field(default_factory=list)
    total_retrieved: int = 0


@dataclass(frozen=True)
class RAGContext:
    """Context for RAG operations."""

    user_query: str
    namespace: str | None = None
    tags: list[str] | None = None
    conversation_id: str | None = None
    user_id: str | None = None
    retrieved_context: RetrievedContext | None = None
    augmented_prompt: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
