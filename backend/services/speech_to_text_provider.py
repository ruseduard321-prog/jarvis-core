from __future__ import annotations

from abc import ABC, abstractmethod

from backend.schemas.assets import TranscriptAsset


class SpeechToTextProvider(ABC):
    """Provider abstraction for speech-to-text transcription. Prepared as a platform
    capability for future forced-alignment subtitle timing; not wired into the
    YouTube production workflow today."""

    @abstractmethod
    async def transcribe(
        self,
        *,
        audio_bytes: bytes,
        filename: str = "audio.mp3",
        language: str | None = None,
    ) -> tuple[TranscriptAsset, str]:
        raise NotImplementedError
