from __future__ import annotations

from datetime import datetime, timezone

from backend.schemas.assets import TranscriptAsset
from backend.services.speech_to_text_provider import SpeechToTextProvider


class DefaultSpeechToTextProvider(SpeechToTextProvider):
    """Default placeholder speech-to-text provider for architecture validation."""

    async def transcribe(
        self,
        *,
        audio_bytes: bytes,
        filename: str = "audio.mp3",
        language: str | None = None,
    ) -> tuple[TranscriptAsset, str]:
        asset = TranscriptAsset(
            provider="default-speech-to-text",
            language=language or "",
            generation_time=datetime.now(timezone.utc).isoformat(),
            status="SKIPPED",
            error="Placeholder provider does not transcribe audio",
        )
        return asset, ""
