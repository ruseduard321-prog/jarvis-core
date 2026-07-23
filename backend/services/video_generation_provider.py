from __future__ import annotations

from abc import ABC, abstractmethod

from backend.core.media_asset import MediaAsset


class VideoGenerationProvider(ABC):
    """Prepared provider abstraction for video generation. No implementation ships
    with F19 — video rendering is out of scope until F20+. Defining the interface now
    lets a future provider register through the same DI pattern without touching
    callers written against this contract."""

    @abstractmethod
    async def generate_video(self, *, prompt: str, duration: float | None = None) -> MediaAsset:
        raise NotImplementedError
