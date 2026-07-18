from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class EmbeddingUsage:
    """Token/computation usage for embeddings."""

    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None


@dataclass(frozen=True)
class EmbeddingRequest:
    """Request to generate embeddings for text inputs."""

    texts: list[str]
    model: str | None = None
    options: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class EmbeddingResponse:
    """Response containing generated embeddings."""

    embeddings: list[list[float]]
    model: str
    usage: EmbeddingUsage | None = None
    raw_response: dict[str, Any] = field(default_factory=dict)
