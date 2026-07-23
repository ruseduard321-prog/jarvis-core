from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from backend.core.media_asset import MediaAsset


class VisionProvider(ABC):
    """Provider abstraction for image understanding services."""

    @abstractmethod
    async def analyze_image(self, *, source: str, prompt: str | None = None) -> tuple[MediaAsset, list[dict[str, Any]]]:
        raise NotImplementedError
