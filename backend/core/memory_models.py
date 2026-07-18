from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class MemoryMetadata:
    """Structured metadata for a memory record."""

    source: str | None = None
    tags: list[str] = field(default_factory=list)
    attributes: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class MemoryRecord:
    """A single memory entry stored by the memory system."""

    id: str
    record_type: str
    content: str
    metadata: MemoryMetadata
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class MemoryQuery:
    """Query parameters for searching memory records."""

    record_type: str | None = None
    source: str | None = None
    tags: list[str] | None = None
    metadata_filters: dict[str, Any] | None = None
    created_after: datetime | None = None
    updated_after: datetime | None = None
    limit: int | None = None
    offset: int | None = None


@dataclass(frozen=True)
class MemoryResult:
    """Result wrapper returned for memory queries."""

    records: list[MemoryRecord]
    total_count: int
