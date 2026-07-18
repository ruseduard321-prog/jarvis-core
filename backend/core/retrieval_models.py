from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class RetrievedDocument:
    """A document retrieved from the knowledge base."""

    id: str
    content: str
    source: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    score: float | None = None


@dataclass(frozen=True)
class RetrievalRequest:
    """Request to retrieve documents from knowledge base."""

    query: str
    namespace: str | None = None
    tags: list[str] | None = None
    metadata_filters: dict[str, Any] | None = None
    limit: int | None = None
    options: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RetrievalResult:
    """Result from retrieval operation."""

    documents: list[RetrievedDocument]
    total_count: int
