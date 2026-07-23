from __future__ import annotations

from abc import ABC, abstractmethod

from backend.core.media_asset import MediaAsset


class SoundEffectProvider(ABC):
    """Provider abstraction for sound-effect selection, mirroring
    MusicGenerationProvider exactly. `LocalAudioLibraryProvider` (F26) is the first
    concrete implementation — a keyword-matched local asset library, zero API cost.
    Defining the interface now lets a future provider (e.g. a licensed SFX API)
    register through the same DI pattern without touching callers written against
    this contract."""

    @abstractmethod
    async def get_sound_effect(self, *, keywords: str) -> MediaAsset:
        raise NotImplementedError
