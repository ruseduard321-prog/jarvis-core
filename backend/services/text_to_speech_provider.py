from __future__ import annotations

from abc import ABC, abstractmethod

from backend.schemas.assets import VoiceAsset


class TextToSpeechProvider(ABC):
    """Provider abstraction for text-to-speech generation."""

    @abstractmethod
    async def generate_speech(
        self,
        *,
        text: str,
        model: str | None = None,
        voice: str | None = None,
        speed: float | None = None,
        language: str | None = None,
        instructions: str | None = None,
    ) -> tuple[VoiceAsset, bytes]:
        raise NotImplementedError
