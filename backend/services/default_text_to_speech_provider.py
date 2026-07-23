from __future__ import annotations

from datetime import datetime, timezone

from backend.schemas.assets import VoiceAsset
from backend.services.text_to_speech_provider import TextToSpeechProvider


class DefaultTextToSpeechProvider(TextToSpeechProvider):
    """Default placeholder text-to-speech provider for architecture validation."""

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
        asset = VoiceAsset(
            provider="default-text-to-speech",
            model=model or "",
            voice=voice or "",
            language=language or "en",
            duration=0.0,
            generation_time=datetime.now(timezone.utc).isoformat(),
            status="SKIPPED",
            error="Placeholder provider does not synthesize audio",
        )
        return asset, b""
