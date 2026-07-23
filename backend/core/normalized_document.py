from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class NormalizedDocument:
    """Common document shape returned by all reader tools."""

    title: str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)
    source: str = ""
    url: str | None = None
    language: str | None = None
    chunks: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "content": self.content,
            "metadata": self.metadata,
            "source": self.source,
            "url": self.url,
            "language": self.language,
            "chunks": self.chunks,
        }
