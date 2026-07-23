from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal

MediaType = Literal["image", "audio", "video"]


@dataclass(frozen=True)
class MediaAsset:
    """Provider-agnostic normalized media asset model for all media tools."""

    id: str
    type: MediaType
    source: str
    provider: str
    mime_type: str
    width: int | None = None
    height: int | None = None
    duration: float | None = None
    prompt: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "source": self.source,
            "provider": self.provider,
            "mime_type": self.mime_type,
            "width": self.width,
            "height": self.height,
            "duration": self.duration,
            "prompt": self.prompt,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
        }
