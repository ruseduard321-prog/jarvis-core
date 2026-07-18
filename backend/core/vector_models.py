from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class VectorMetadata:
    """Structured metadata associated with a vector record."""

    source: str | None = None
    tags: list[str] = field(default_factory=list)
    namespace: str | None = None
    attributes: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class VectorRecord:
    """A stored vector with metadata and provenance."""

    id: str
    vector: list[float]
    metadata: VectorMetadata
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class VectorQuery:
    """Query criteria for retrieving vectors."""

    namespace: str | None = None
    tags: list[str] | None = None
    metadata_filters: dict[str, Any] | None = None
    limit: int | None = None
    offset: int | None = None


@dataclass(frozen=True)
class VectorSearchResult:
    """Result wrapper returned for vector queries."""

    records: list[VectorRecord]
    total_count: int
