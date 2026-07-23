from __future__ import annotations

from abc import ABC, abstractmethod

from backend.core.media_asset import MediaAsset


class MusicGenerationProvider(ABC):
    """Prepared provider abstraction for music generation. No implementation ships
    with F19 — actual music synthesis is out of scope; `MusicPlan`/`music.md` only
    document direction. Defining the interface now lets a future provider register
    through the same DI pattern without touching callers written against this contract."""

    @abstractmethod
    async def generate_music(self, *, prompt: str, duration: float | None = None) -> MediaAsset:
        raise NotImplementedError
